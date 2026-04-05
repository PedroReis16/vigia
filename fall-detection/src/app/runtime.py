"""Loop principal: captura de vídeo, pose YOLO e gravação opcional de CSV/stream."""

from __future__ import annotations

import os
import shutil
import time
from dataclasses import dataclass
from typing import Optional

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


def _execute_role(ctx: _CaptureLoopContext) -> None:
    try:
        if ctx.capture_per_second <= 0:
            raise ValueError("capture_per_second must be greater than 0")

        capture_interval = 1.0 / ctx.capture_per_second
        _last_auto_capture = time.monotonic()
        _csv_segment_start: float | None = None
        _csv_segment_index = 0
        _pose_capture_seq = 0

        while True:
            ret, frame = ctx.cap.read()
            if not ret:
                break

            now = time.monotonic()

            if now - _last_auto_capture >= capture_interval:
                person_data = ctx.pose_model.capture_frame(frame)
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
                    _append_pose_csv(
                        csv_path, person_data, capture_seq=_pose_capture_seq
                    )
                    _pose_capture_seq += 1
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
