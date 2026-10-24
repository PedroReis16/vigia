"""CLI e contexto compartilhado do vigia-lab.

    python -m vigia_lab                                   # interface para a Ana (janela)
    python -m vigia_lab --replay clip.mp4 --scenario sentando --duration 8   # sem câmera/janela
    python -m vigia_lab --scenario queda_de_frente        # câmera, sem janela
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from vigia_lab import bootstrap
from vigia_lab.catalog import Scenario, load_catalog
from vigia_lab.manifest import takes_for_scenario
from vigia_lab.takes import new_session_id, next_take_number, takes_from_filenames

DEFAULT_CAPTURES = bootstrap.LAB_ROOT / "captures"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="vigia_lab")
    ap.add_argument("--source", default="0", help="índice da câmera (padrão 0)")
    ap.add_argument("--replay", type=Path, help="vídeo para reproduzir no lugar da câmera")
    ap.add_argument("--scenario", help="id do cenário; sem ele abre a interface com janela")
    ap.add_argument("--duration", type=float, default=10.0, help="duração da gravação (s)")
    ap.add_argument("--countdown", type=float, default=3.0)
    ap.add_argument("--out", type=Path, default=DEFAULT_CAPTURES)
    ap.add_argument("--min-frames", type=int, default=10, help="frames de tronco válido p/ manter um track")
    ap.add_argument("--ids", choices=("baseline", "grace"), default="baseline",
                    help="baseline = como o vigia; grace = tolera 1,5 s sem ver a pessoa e ignora deteccoes sem ID")
    ap.add_argument("--no-video", action="store_true", help="não gravar o vídeo bruto")
    return ap


@dataclass
class LabContext:
    """Tudo que é caro de criar e vale para a sessão inteira."""

    out: Path
    session_id: str
    settings: Any
    kwargs: dict[str, Any]
    model: Any
    scenarios: list[Scenario]

    @property
    def manifest(self) -> Path:
        return self.out / "manifest.csv"

    def next_take(self, scenario_id: str) -> int:
        return next_take_number(
            takes_for_scenario(self.manifest, scenario_id)
            | takes_from_filenames(self.out / scenario_id, scenario_id)
        )


def make_context(out: Path) -> LabContext:
    from capture.yolo_model import get_yolo_model
    from shared.settings import get_settings

    from vigia_lab import pose_source
    from vigia_lab.models_gru import verify_lock

    bootstrap.verify_onboard_origin()
    verify_lock()
    kwargs = pose_source.read_stream_kwargs()
    if not pose_source.stream_calls_model_track_with_kwargs():
        raise RuntimeError("_stream_results do onboard mudou; revisar pose_source.py")
    return LabContext(
        out=out, session_id=new_session_id(), settings=get_settings(), kwargs=kwargs,
        model=get_yolo_model(), scenarios=load_catalog(),
    )


def record_take(
    ctx: LabContext,
    scenario: Scenario,
    *,
    source: int | str,
    replay: bool,
    duration: float,
    countdown: float,
    min_frames: int,
    ids_mode: str = "baseline",
    save_video: bool = True,
    on_frame: Callable | None = None,
    should_stop: Callable[[], bool] = lambda: False,
    pending_marks: Callable[[], int] = lambda: 0,
    operator_note: str = "",
    extra_quality: Callable[[], dict] | None = None,
    on_result: Callable[[str, list[str], dict, Path | None], bool] | None = None,
) -> tuple[str, list[str], dict] | None:
    """Grava UMA tomada. `on_result(cor, motivos, qualidade, take_dir)` pode devolver
    False para o operador descartar (então nada é registrado no manifest)."""
    from core.models.person_runtime import get_person_runtime_store
    from core.point_filter import filter_observations
    from shared.yolo_export import ensure_yolo_pose_export, read_exported_imgsz

    from vigia_lab import pose_source
    from vigia_lab.fingerprint import build_fingerprint
    from vigia_lab.models_gru import build_classifiers
    from vigia_lab.recorder import take_paths
    from vigia_lab.session import TakeConfig, finalize_take, run_take
    from vigia_lab.video_sink import VideoSink

    take = ctx.next_take(scenario.id)
    cfg = TakeConfig(
        duration_s=duration, countdown_s=0.0 if replay else countdown,
        frame_rate=ctx.settings.frame_rate, min_frames_per_person=min_frames, ids_mode=ids_mode,
    )
    pose_source.reset_tracker(ctx.model)
    classifiers = build_classifiers(ctx.settings.slider_window_size)
    nominal = pose_source.native_fps(source)
    frames = pose_source.iter_pose_frames(ctx.model, source, ctx.kwargs, clock="video" if replay else "wall")
    paths = take_paths(ctx.out, scenario.id, take)

    sink_holder: dict[str, Any] = {}

    class _LazySink:
        """Cria o VideoWriter no 1º frame (só então se sabe o tamanho da imagem)."""

        def write(self, image) -> None:
            if "sink" not in sink_holder:
                h, w = image.shape[:2]
                sink_holder["sink"] = VideoSink(paths["video"], nominal or 30.0, (w, h))
            sink_holder["sink"].write(image)

    lazy = _LazySink() if save_video else None
    outcome = run_take(
        frames, cfg, classifiers, filter_observations, get_person_runtime_store,
        on_frame=on_frame, video_sink=lazy, should_stop=should_stop, pending_marks=pending_marks,
        cpu_sampler=_cpu_sampler(),
    )
    sink = sink_holder.get("sink")
    if sink is not None:
        sink.close()
    if outcome is None:
        return None

    fingerprint = fingerprint_for(ctx)
    color, reasons, q = finalize_take(
        outcome, captures_dir=ctx.out, manifest_path=ctx.manifest, scenario_id=scenario.id,
        scenario_label=scenario.label, take=take, session_id=ctx.session_id,
        fingerprint=fingerprint, camera_fps_nominal=nominal, cfg=cfg,
        video_drops=sink.drops if sink else 0, operator_note=operator_note,
        write_manifest=False, extra_quality=extra_quality() if extra_quality else None,
    )
    keep = on_result(color, reasons, q, paths["dir"]) if on_result else True
    if keep:
        _register(ctx, outcome, scenario, take, cfg, color)
    else:
        _discard_files(paths["dir"], scenario.id, take)
    return color, reasons, q


def fingerprint_for(ctx: LabContext) -> dict[str, Any]:
    """Ficha técnica da sessão (modelo de pose, parâmetros efetivos, versões, hashes, SHA)."""
    from shared.yolo_export import ensure_yolo_pose_export, read_exported_imgsz

    from vigia_lab.fingerprint import build_fingerprint

    predictor = getattr(ctx.model, "predictor", None)
    pargs = vars(predictor.args) if predictor is not None and hasattr(predictor, "args") else None
    weights = Path(ensure_yolo_pose_export(ctx.settings.yolo_model))
    return build_fingerprint(
        stream_kwargs=ctx.kwargs, yolo_weights=weights, predictor_args=pargs, settings=ctx.settings,
        imgsz_onnx=read_exported_imgsz(weights, "onnx") if weights.suffix == ".onnx" else None,
    )


def _cpu_sampler() -> Callable[[], float]:
    """CPU total do sistema (%) desde a chamada anterior; 0 se psutil faltar."""
    try:
        import psutil

        psutil.cpu_percent(None)
        return lambda: float(psutil.cpu_percent(None))
    except Exception:
        return lambda: 0.0


def _register(ctx, outcome, scenario, take, cfg, color) -> None:
    """Escreve a linha do manifest de uma tomada aceita (releitura dos clipes gravados)."""
    from vigia_lab.manifest import ManifestEntry, append_entries
    from vigia_lab.recorder import take_paths
    from vigia_lab.takes import clip_id, take_id

    rec = outcome.recorder
    paths = take_paths(ctx.out, scenario.id, take)
    fps = (len(rec.frames) - 1) / outcome.duration_s if outcome.duration_s > 0 else 0.0
    event_t = rec.marks[0] if rec.marks else None
    entries = [
        ManifestEntry(
            clip_id=clip_id(scenario.id, take, idx), is_fall=scenario.is_fall, src_fps=round(fps, 3),
            lbl_path=paths["dir"] / f"{clip_id(scenario.id, take, idx)}_labels.npy",
            group_id=take_id(scenario.id, take),
            px_path=paths["dir"] / f"{clip_id(scenario.id, take, idx)}.npy",
            scenario_id=scenario.id, scenario_label=scenario.label, take_number=take, person_idx=idx,
            n_frames=len(rec.frames), session_id=ctx.session_id, event_t=event_t,
            video_path=paths["video"] if paths["video"].exists() else None,
            quality_verdict=color, meta_path=paths["meta"],
        )
        for idx, _ in enumerate(rec.person_tracks(cfg.min_frames_per_person))
    ]
    append_entries(ctx.manifest, entries)


def _discard_files(scenario_dir: Path, scenario_id: str, take: int) -> None:
    from vigia_lab.takes import take_id

    prefix = take_id(scenario_id, take)
    for p in scenario_dir.glob(f"{prefix}*"):
        p.unlink(missing_ok=True)


SUBCOMMANDS = ("record", "process", "report")


def _float_list(text: str) -> list[float]:
    return [float(x) for x in text.split(",") if x.strip()]


def build_subparser(name: str) -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog=f"vigia_lab {name}")
    if name == "record":
        ap.add_argument("--source", type=int, default=0, help="indice da camera")
        ap.add_argument("--duration", type=float, default=10.0, help="duracao fixa (s); a tecla d alterna p/ manual")
        ap.add_argument("--resolution", default="640x480", help="igual a da camera da Raspberry")
        ap.add_argument("--fps", type=int, default=30)
        ap.add_argument("--out", type=Path, default=DEFAULT_CAPTURES)
    elif name == "process":
        ap.add_argument("--captures", type=Path, default=DEFAULT_CAPTURES)
        ap.add_argument("--out", type=Path, default=bootstrap.LAB_ROOT / "reprocessed")
        ap.add_argument("--pose-fps", default="10", help="cadencias do pose a simular, ex.: 6,8,10,15")
        ap.add_argument("--ids", default="baseline", help="baseline,grace")
        ap.add_argument("--only", help="so clipes cujo nome contenha este texto")
    else:
        ap.add_argument("--root", type=Path, default=bootstrap.LAB_ROOT / "reprocessed")
    return ap


def run_subcommand(name: str, argv: list[str]) -> int:
    args = build_subparser(name).parse_args(argv)
    if name == "report":
        from vigia_lab import report

        per_take, summary_csv, summary_md = report.write_outputs(args.root)
        print(summary_md.read_text(encoding="utf-8") if summary_md.exists() else "sem dados")
        print(f"arquivos: {per_take}, {summary_csv}, {summary_md}")
        return 0

    ctx = make_context(args.out if name == "record" else args.captures)
    if name == "record":
        from vigia_lab.lite_ui import run_recorder

        return run_recorder(ctx, args)

    from vigia_lab import offline, report

    ids_list = [x.strip() for x in args.ids.split(",") if x.strip()]
    bad = [x for x in ids_list if x not in ("baseline", "grace")]
    if bad:
        print(f"--ids invalido: {bad}")
        return 2
    results = offline.process_dir(
        ctx, args.captures, pose_fps_list=_float_list(args.pose_fps), ids_list=ids_list,
        out_root=args.out, only=args.only,
    )
    if not results:
        print(f"nenhum *_capture.json em {args.captures}/<cenario>/")
        return 1
    _, _, summary_md = report.write_outputs(args.out)
    print("\n" + summary_md.read_text(encoding="utf-8"))
    return 0


def main(argv: list[str] | None = None) -> int:
    import sys

    argv = sys.argv[1:] if argv is None else argv
    if argv and argv[0] in SUBCOMMANDS:
        return run_subcommand(argv[0], argv[1:])
    args = build_parser().parse_args(argv)
    ctx = make_context(args.out)

    if args.scenario is None:
        from vigia_lab.ui import run_ui

        return run_ui(ctx, args)

    scenario = next((s for s in ctx.scenarios if s.id == args.scenario), None)
    if scenario is None:
        print(f"cenário desconhecido: {args.scenario}\nválidos: {', '.join(s.id for s in ctx.scenarios)}")
        return 2
    source: int | str = str(args.replay) if args.replay else int(args.source)
    print(f"Gravando {scenario.id} ({scenario.label}), {args.duration:.0f}s...")
    result = record_take(
        ctx, scenario, source=source, replay=bool(args.replay), duration=args.duration,
        countdown=args.countdown, min_frames=args.min_frames, ids_mode=args.ids,
        save_video=not args.no_video,
    )
    if result is None:
        print("Tomada não iniciada (sem frames).")
        return 1
    color, reasons, q = result
    print(f"Veredito: {color.upper()} — {'; '.join(reasons)}")
    print(f"fps do pose {q['pose_fps']:.1f} | entregues {q['delivered_fps']:.1f}/s | "
          f"tracks {q['n_tracks']} | tronco válido {q['torso_valid_frac']:.0%}")
    if "bottleneck" in q:
        print(f"laço {q['loop_dt_ms_mean']:.0f} ms/frame: YOLO {q['yolo_ms_mean']:.0f} + espera camera/tracker "
              f"{q['source_wait_ms_mean']:.0f} + nosso codigo {q['consumer_ms_mean']:.0f} | "
              f"CPU {q['cpu_pct_mean']:.0f}% (max {q['cpu_pct_max']:.0f}%) | gargalo: {q['bottleneck']}")
    return 0
