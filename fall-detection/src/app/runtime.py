"""Loop principal: captura de vídeo, pose YOLO e gravação opcional de CSV/stream."""

from __future__ import annotations

import os
import queue
import shutil
import threading
import time
from dataclasses import dataclass
from typing import Any, Optional

import cv2
import pandas as pd

from app.capture.frame_data import PersonData
from app.capture.pose_model import PoseModel
from app.capture.workers import FrameSaveWorker, StreamOutWorker, optional_stream_worker
from app.config import Settings

@dataclass
class _CaptureLoopContext:
    cap: cv2.VideoCapture
    show_video: bool
    pose_model: PoseModel
    capture_per_second: int
    pose_csv_dir: str | None
    pose_csv_window_seconds: float
    stream: Optional[StreamOutWorker]
    saver: Optional[FrameSaveWorker]


def _frame_rows(
    frame_data: list[PersonData], *, capture_seq: int
) -> list[dict[str, object]]:
    lines: list[dict[str, object]] = []
    for person in frame_data:
        for body_data in person.body_data:
            lines.append(
                {
                    "capture_seq": capture_seq,
                    "person_id": person.person_id,
                    "label": body_data.label,
                    "x": body_data.x,
                    "y": body_data.y,
                    "conf": body_data.conf,
                }
            )
    return lines


def _append_pose_csv(path: str, frame_data: list[PersonData], *, capture_seq: int) -> None:
    lines = _frame_rows(frame_data, capture_seq=capture_seq)
    if not lines:
        return
    write_header = not os.path.isfile(path)
    df = pd.DataFrame(lines)
    df.to_csv(path, index=False, mode="w" if write_header else "a", header=write_header)


@dataclass(frozen=True)
class _PoseProcessJob:
    """Frame já copiado; path e capture_seq definidos na thread de captura."""

    frame: Any
    csv_path: str | None
    capture_seq: int


def _pose_worker_loop(pose_model: PoseModel, work_q: "queue.Queue[_PoseProcessJob | None]") -> None:
    while True:
        job = work_q.get()
        if job is None:
            work_q.task_done()
            break
        try:
            person_data = pose_model.capture_frame(job.frame)
            if job.csv_path is not None:
                _append_pose_csv(job.csv_path, person_data, capture_seq=job.capture_seq)
        finally:
            work_q.task_done()


def _execute_role(ctx: _CaptureLoopContext) -> None:
    pose_work_q: queue.Queue[_PoseProcessJob | None] | None = None
    pose_worker: threading.Thread | None = None
    try:
        if ctx.capture_per_second <= 0:
            raise ValueError("capture_per_second must be greater than 0")

        capture_interval = 1.0 / ctx.capture_per_second
        _last_auto_capture = time.monotonic()
        _csv_segment_start: float | None = None
        _csv_segment_index = 0
        _pose_capture_seq = 0

        # Fila acoplada: se o worker atrasar, a captura espera em put() (evita fila infinita).
        pose_work_q = queue.Queue(maxsize=4)
        pose_worker = threading.Thread(
            target=_pose_worker_loop,
            args=(ctx.pose_model, pose_work_q),
            name="pose-csv-worker",
            daemon=True,
        )
        pose_worker.start()

        while True:
            ret, frame = ctx.cap.read()
            if not ret:
                break

            now = time.monotonic()

            if now - _last_auto_capture >= capture_interval:
                csv_path: str | None = None
                if ctx.pose_csv_dir is not None:
                    new_segment = (
                        _csv_segment_start is None
                        or (now - _csv_segment_start) >= ctx.pose_csv_window_seconds
                    )
                    if new_segment:
                        if _csv_segment_start is not None:
                            _csv_segment_index += 1
                        _csv_segment_start = now
                    csv_path = os.path.join(
                        ctx.pose_csv_dir, f"poses_{_csv_segment_index:06d}.csv"
                    )
                seq = _pose_capture_seq
                _pose_capture_seq += 1
                pose_work_q.put(
                    _PoseProcessJob(frame=frame.copy(), csv_path=csv_path, capture_seq=seq)
                )
                _last_auto_capture = now

            if ctx.stream is not None:
                ctx.stream.send_frame(frame)

            if ctx.show_video:
                frame = cv2.flip(frame, 1)
                cv2.imshow("Detection", frame)
                key = cv2.waitKey(1) & 0xFF
                if key == ord("q"):
                    break

    finally:
        if pose_work_q is not None:
            pose_work_q.put(None)
        if pose_worker is not None:
            pose_worker.join(timeout=120.0)
        ctx.cap.release()
        cv2.destroyAllWindows()
        if ctx.stream is not None:
            ctx.stream.stop()
        if ctx.saver is not None:
            ctx.saver.stop()


def run(settings: Settings) -> None:
    """Configura captura, workers opcionais e loop principal de vídeo/pose."""
    pose_csv_dir: str | None = None
    if settings.data_path:
        if settings.pose_csv_window_seconds <= 0:
            raise ValueError("pose_csv_window_seconds must be greater than 0")
        print(f"Removing data path: {settings.data_path}")
        if os.path.isdir(settings.data_path):
            shutil.rmtree(settings.data_path)
        os.makedirs(settings.data_path, exist_ok=True)
        if settings.frames_dir:
            os.makedirs(settings.frames_dir, exist_ok=True)
        pose_csv_dir = settings.data_path

    stream: Optional[StreamOutWorker] | None = None

    if settings.stream_video:
        stream = optional_stream_worker(
            settings.stream_ingest_url,
            settings.stream_ingest_token,
            settings.stream_target,
        )

    saver: FrameSaveWorker | None = None
    if settings.frames_dir:
        saver = FrameSaveWorker()
        saver.start()

    cap = cv2.VideoCapture(settings.video_capture_source)

    pose_model = PoseModel(model_path=settings.yolo_pose_model, device=settings.yolo_model_device)
    show_video = settings.show_video

    _execute_role(
        _CaptureLoopContext(
            cap=cap,
            show_video=show_video,
            pose_model=pose_model,
            capture_per_second=settings.captures_per_second,
            pose_csv_dir=pose_csv_dir,
            pose_csv_window_seconds=settings.pose_csv_window_seconds,
            stream=stream,
            saver=saver,
        )
    )
