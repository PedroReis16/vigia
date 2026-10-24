"""Processamento offline: vídeo gravado -> YOLO/tracker -> 3 modelos, com a cadência do dispositivo simulada.

Fluxo por clipe:
  1. `select_frames(t_rel, pose_fps)`: só esses frames chegam ao YOLO/tracker (como na Raspberry);
  2. o tracker é alimentado frame a frame (`model.track(frame, persist=True, ...)`, validado como
     idêntico ao modo `stream` em IDs e keypoints);
  3. cada resultado vira um `PoseFrame` com o TEMPO REAL do sidecar (não o fps do contêiner);
  4. `session.run_take` aplica throttle + filtro + 3 modelos exatamente como no ao vivo.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any, Iterator

import numpy as np

from vigia_lab.cadence import select_frames
from vigia_lab.onset import trunk_onset
from vigia_lab.session import PoseFrame, TakeConfig, finalize_take, run_take
from vigia_lab.sidecar import FrameClock, load_capture_meta, load_frames, sidecar_paths

_FOREVER = 1e9


def iter_offline_frames(
    model: Any, video_path: Path, clock: FrameClock, selected: np.ndarray, kwargs: dict[str, Any],
) -> Iterator[PoseFrame]:
    import cv2

    from capture.pose_extract import unpack_raw_points
    from vigia_lab.pose_source import is_untracked

    keep = set(int(i) for i in selected)
    cap = cv2.VideoCapture(str(video_path))
    try:
        i = -1
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            i += 1
            if i >= len(clock):
                break
            if i not in keep:
                continue
            t0 = time.perf_counter()
            result = model.track(frame, **kwargs)[0]
            wait_ms = (time.perf_counter() - t0) * 1000.0
            speed = getattr(result, "speed", None) or {}
            t_wall, t_mono = float(clock.t_wall[i]), float(clock.t_mono[i])
            yield PoseFrame(
                observations=unpack_raw_points(result, timestamp=t_wall),
                image=frame,
                yolo_ms=float(sum(speed.get(k, 0.0) for k in ("preprocess", "inference", "postprocess"))),
                t_wall=t_wall,
                t_mono=t_mono,
                untracked=is_untracked(result),
                wait_ms=wait_ms,
            )
    finally:
        cap.release()


def tag_for(pose_fps: float, ids_mode: str) -> str:
    return f"fps{pose_fps:g}_{ids_mode}"


def process_take(
    ctx: Any, capture_json: Path, *, pose_fps: float, ids_mode: str, out_root: Path,
) -> dict[str, Any]:
    """Reprocessa UM clipe. `capture_json` = `<take>_capture.json` (ao lado do `.avi` e do `_frames.npz`)."""
    from core.models.person_runtime import get_person_runtime_store
    from core.point_filter import filter_observations

    from vigia_lab import pose_source
    from vigia_lab.app import fingerprint_for
    from vigia_lab.models_gru import build_classifiers

    meta = load_capture_meta(capture_json)
    video_path = Path(meta["video_path"]) if Path(meta["video_path"]).exists() else capture_json.with_name(
        capture_json.name.replace("_capture.json", ".avi")
    )
    clock = load_frames(sidecar_paths(video_path)["frames"])
    scenario_id, label, take = meta["scenario_id"], meta["scenario_label"], int(meta["take_number"])
    marks = meta.get("marks") or {}

    selected = select_frames(clock.t_rel, pose_fps)
    kwargs = {k: v for k, v in ctx.kwargs.items() if k != "stream"}
    pose_source.reset_tracker(ctx.model)
    classifiers = build_classifiers(ctx.settings.slider_window_size)
    cfg = TakeConfig(
        duration_s=_FOREVER, countdown_s=0.0, frame_rate=ctx.settings.frame_rate, ids_mode=ids_mode,
    )
    frames = iter_offline_frames(ctx.model, video_path, clock, selected, kwargs)
    outcome = run_take(frames, cfg, classifiers, filter_observations, get_person_runtime_store)
    pose_source.reset_tracker(ctx.model)
    if outcome is None:
        raise RuntimeError(f"nenhum frame processado em {video_path}")

    rec = outcome.recorder
    tracks = rec.person_tracks(cfg.min_frames_per_person)
    onset_auto = trunk_onset(rec.t_rel(), tracks[0][1]) if tracks else None
    start = marks.get("event_start_t")
    if start is not None:
        rec.marks.append(float(start))

    tag = tag_for(pose_fps, ids_mode)
    extra = {
        "source": "offline",
        "source_video": str(video_path),
        "pose_fps_simulated": pose_fps,
        "frames_in_video": len(clock),
        "frames_processed": int(len(selected)),
        "event_start_t": start,
        "event_end_t": marks.get("event_end_t"),
        "event_t_auto": onset_auto,
        "mark_vs_auto_lag_s": (start - onset_auto) if (start is not None and onset_auto is not None) else None,
        "capture_quality": meta.get("capture_quality"),
        "tag": tag,
    }
    color, reasons, q = finalize_take(
        outcome, captures_dir=out_root / tag, manifest_path=out_root / tag / "manifest.csv",
        scenario_id=scenario_id, scenario_label=label, take=take, session_id=tag,
        fingerprint=fingerprint_for(ctx), camera_fps_nominal=meta.get("nominal_fps"), cfg=cfg,
        write_manifest=False, extra_meta=extra,
    )
    return {"tag": tag, "take": f"{scenario_id}_take{take:02d}", "verdict": color, "reasons": reasons, "quality": q}


def find_captures(captures_dir: Path) -> list[Path]:
    return sorted(captures_dir.glob("*/*_capture.json"))


def process_dir(
    ctx: Any, captures_dir: Path, *, pose_fps_list: list[float], ids_list: list[str], out_root: Path,
    only: str | None = None, log=print,
) -> list[dict[str, Any]]:
    results = []
    jsons = [j for j in find_captures(captures_dir) if only is None or only in j.name]
    for j in jsons:
        for fps in pose_fps_list:
            for ids_mode in ids_list:
                r = process_take(ctx, j, pose_fps=fps, ids_mode=ids_mode, out_root=out_root)
                log(f"{r['take']:36s} {r['tag']:16s} entregues {r['quality']['delivered_fps']:.1f}/s  "
                    f"untracked {r['quality']['untracked_frames']}  id_changes {r['quality']['id_set_changes_delivered']}")
                results.append(r)
    return results
