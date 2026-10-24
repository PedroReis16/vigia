"""Uma tomada: laço de frames -> throttle -> classificadores -> gravação.

`run_take` não conhece câmera, YOLO nem janela: consome um iterável de
`PoseFrame` (produzido por `pose_source`) e chama hooks opcionais. Isso permite
testar o laço com frames sintéticos e reutilizá-lo no replay de vídeo.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping

import numpy as np

from core.models.types import PoseObservation
from vigia_lab.delivery import deliver_batch
from vigia_lab.idpolicy import IdGrace
from vigia_lab.manifest import ManifestEntry, append_entries
from vigia_lab.quality import Thresholds, compute_quality, timing_summary, verdict
from vigia_lab.recorder import FrameRecord, TakeRecorder, take_paths
from vigia_lab.takes import take_id
from vigia_lab.throttle import Throttle


@dataclass
class PoseFrame:
    """Um resultado do YOLO já convertido (timestamps tirados DEPOIS da inferência)."""

    observations: list[PoseObservation]
    image: np.ndarray | None
    yolo_ms: float
    t_wall: float
    t_mono: float
    untracked: bool = False   # detecções SEM boxes.id (o vigia numera 0..n-1)
    wait_ms: float = 0.0      # tempo bloqueado esperando este resultado (câmera + YOLO + tracker)


@dataclass(frozen=True)
class TakeConfig:
    duration_s: float = 10.0
    countdown_s: float = 3.0
    frame_rate: int = 12
    min_frames_per_person: int = 10
    ids_mode: str = "baseline"       # 'baseline' = vigia; 'grace' = tolerância + ignora sem ID
    grace_s: float = 1.5


@dataclass
class TakeOutcome:
    recorder: TakeRecorder
    duration_s: float
    aborted: bool
    throttle_dropped: int
    classifier_ms_total: float


def brightness(image: np.ndarray | None) -> float:
    if image is None:
        return 0.0
    return float(image[::8, ::8].mean())


def run_take(
    frames: Iterable[PoseFrame],
    cfg: TakeConfig,
    classifiers: Mapping[str, Any],
    filter_fn: Callable[[list[PoseObservation]], list[PoseObservation]],
    runtime_store_fn: Callable[[], Any],
    on_frame: Callable[[PoseFrame, str, float, "TakeRecorder | None"], None] | None = None,
    video_sink: Any = None,
    should_stop: Callable[[], bool] = lambda: False,
    pending_marks: Callable[[], int] = lambda: 0,
    cpu_sampler: Callable[[], float] | None = None,
) -> TakeOutcome | None:
    """Devolve None se a contagem regressiva foi interrompida; `aborted=True` se
    abortada durante a gravação. `on_frame(frame, fase, tempo_restante, recorder)`
    com fase 'countdown' ou 'recording'."""
    rec = TakeRecorder()
    throttle: Throttle | None = None
    grace = IdGrace(cfg.grace_s) if cfg.ids_mode == "grace" else None
    now = [0.0]
    count_t0: float | None = None
    rec_t0: float | None = None
    classifier_ms = 0.0
    marks_seen = 0
    idx = 0

    for frame in frames:
        if should_stop():
            return None if rec_t0 is None else _outcome(rec, throttle, classifier_ms, True)

        if rec_t0 is None:
            count_t0 = frame.t_mono if count_t0 is None else count_t0
            remaining = cfg.countdown_s - (frame.t_mono - count_t0)
            if on_frame:
                on_frame(frame, "countdown", max(remaining, 0.0), None)
            if remaining > 0:
                continue
            rec_t0 = frame.t_mono
            throttle = Throttle(cfg.frame_rate, clock=lambda: now[0])

        body_t0 = time.perf_counter()
        now[0] = frame.t_mono
        delivered = throttle.accept()
        batch = frame.observations
        if grace is not None and frame.untracked:
            batch = []                       # sem ID do tracker: não vira pessoa 0,1,...
        record = FrameRecord(
            frame_idx=idx,
            t_wall=frame.t_wall,
            t_mono=frame.t_mono,
            person_ids=[-1] * len(frame.observations) if batch != frame.observations else [o.person_id for o in batch],
            untracked=frame.untracked,
            wait_ms=frame.wait_ms,
            cpu_pct=cpu_sampler() if cpu_sampler else 0.0,
            keypoints=[np.asarray(o.keypoints, dtype=np.float32) for o in batch],
            delivered=delivered,
            yolo_ms=frame.yolo_ms,
            brightness=brightness(frame.image),
        )
        if delivered:
            active_fn = (lambda ids, t=frame.t_mono: grace.active(ids, t)) if grace else None
            result = deliver_batch(batch, classifiers, filter_fn, runtime_store_fn, active_fn)
            record.n_filtered = result.n_filtered
            record.reset_all = result.reset_all
            rec.add_frame(record)
            for name, items in result.decisions.items():
                rec.add_decisions(idx, frame.t_wall, name, items, result.latency_ms[name])
                classifier_ms += result.latency_ms[name]
        else:
            rec.add_frame(record)

        while marks_seen < pending_marks():
            rec.mark_event(frame.t_wall)
            marks_seen += 1
        if video_sink is not None and frame.image is not None:
            video_sink.write(frame.image)

        elapsed = frame.t_mono - rec_t0
        if on_frame:
            on_frame(frame, "recording", max(cfg.duration_s - elapsed, 0.0), rec)
        record.consumer_ms = (time.perf_counter() - body_t0) * 1000.0
        idx += 1
        if elapsed >= cfg.duration_s:
            break

    if rec_t0 is None:
        return None
    return _outcome(rec, throttle, classifier_ms, False)


def _outcome(rec: TakeRecorder, throttle: Throttle | None, ms: float, aborted: bool) -> TakeOutcome:
    t = rec.t_wall()
    return TakeOutcome(
        recorder=rec,
        duration_s=float(t[-1] - t[0]) if len(t) > 1 else 0.0,
        aborted=aborted,
        throttle_dropped=throttle.dropped if throttle else 0,
        classifier_ms_total=ms,
    )


def finalize_take(
    outcome: TakeOutcome,
    *,
    captures_dir: Path,
    manifest_path: Path,
    scenario_id: str,
    scenario_label: str,
    take: int,
    session_id: str,
    fingerprint: dict[str, Any],
    camera_fps_nominal: float | None,
    cfg: TakeConfig,
    video_drops: int = 0,
    operator_note: str = "",
    thresholds: Thresholds = Thresholds(),
    write_manifest: bool = True,
    extra_quality: dict[str, Any] | None = None,
    extra_meta: dict[str, Any] | None = None,
) -> tuple[str, list[str], dict[str, Any]]:
    """Grava clipes/raw/decisions/meta e (opcional) o manifest. Devolve (cor, motivos, qualidade)."""
    rec = outcome.recorder
    paths = take_paths(captures_dir, scenario_id, take)
    name = take_id(scenario_id, take)
    is_fall = scenario_label == "FALL"
    paths["dir"].mkdir(parents=True, exist_ok=True)

    clips = rec.save_clips(paths["dir"], scenario_id, take, is_fall, cfg.min_frames_per_person)
    rec.save_raw(paths["raw"])
    rec.save_decisions(paths["decisions"], name)

    tracks = rec.person_tracks(cfg.min_frames_per_person)
    t = rec.t_wall()
    torso = rec.torso_valid_any(cfg.min_frames_per_person)
    confs = [
        float(kp[:, :, 2][kp[:, :, 2] > 0].mean()) for _pid, kp in tracks if (kp[:, :, 2] > 0).any()
    ]
    event_t = rec.marks[0] if rec.marks else None
    event_window = (max(event_t - 1.0, 0.0), event_t + 3.0) if event_t is not None else None
    quality = compute_quality(
        t_wall=t,
        delivered=np.array([f.delivered for f in rec.frames], dtype=bool),
        yolo_ms=np.array([f.yolo_ms for f in rec.frames], dtype=np.float64),
        torso_valid=torso,
        brightness=np.array([f.brightness for f in rec.frames], dtype=np.float64),
        n_tracks=len(tracks),
        mean_conf=float(np.mean(confs)) if confs else 0.0,
        camera_fps_nominal=camera_fps_nominal,
        video_drops=video_drops,
        event_window=event_window,
    )
    quality["classifier_ms_total"] = outcome.classifier_ms_total
    quality.update(rec.id_stats())
    quality.update(timing_summary(
        rec.t_wall(), rec.wait_ms(), rec.yolo_ms(), rec.consumer_ms(), rec.cpu_pct(),
    ))
    quality.update(extra_quality or {})
    color, reasons = verdict(quality, thresholds)

    meta = {
        "take": name,
        "scenario_id": scenario_id,
        "scenario_label": scenario_label,
        "session_id": session_id,
        "duration_requested_s": cfg.duration_s,
        "aborted": outcome.aborted,
        "ids_mode": cfg.ids_mode,
        "grace_s": cfg.grace_s if cfg.ids_mode == "grace" else None,
        "event_t_key": event_t,
        "quality": quality,
        "verdict": {"color": color, "reasons": reasons},
        "fingerprint": fingerprint,
        **(extra_meta or {}),
        "recorded_at_unix": time.time(),
    }
    rec.save_meta(paths["meta"], meta)

    if write_manifest and clips:
        fps = quality.get("pose_fps", 0.0)
        append_entries(manifest_path, [
            ManifestEntry(
                clip_id=c.clip_id, is_fall=is_fall, src_fps=round(fps, 3),
                lbl_path=c.lbl_path, group_id=name, px_path=c.px_path,
                scenario_id=scenario_id, scenario_label=scenario_label, take_number=take,
                person_idx=c.person_idx, n_frames=c.n_frames, session_id=session_id,
                operator_note=operator_note, event_t=event_t,
                video_path=paths["video"] if paths["video"].exists() else None,
                quality_verdict=color, meta_path=paths["meta"],
            )
            for c in clips
        ])
    return color, reasons, quality
