"""Loop contínuo: leitura da câmera, enfileiramento de pose/CSV, stream e preview."""

from __future__ import annotations

import os
import queue
import threading
import time
from dataclasses import dataclass

import cv2

from app.capture.io.workers import FrameSaveWorker, StreamOutWorker
from app.capture.pose.pose_model import PoseModel
from app.capture.pose.pose_process_worker import PoseProcessJob, pose_worker_loop


@dataclass
class CaptureLoopContext:
    cap: cv2.VideoCapture
    show_video: bool
    pose_model: PoseModel
    capture_per_second: int
    pose_csv_dir: str | None
    pose_csv_window_seconds: float
    stream: StreamOutWorker | None
    saver: FrameSaveWorker | None


def run_capture_loop(ctx: CaptureLoopContext) -> None:
    pose_work_q: queue.Queue[PoseProcessJob | None] | None = None
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
            target=pose_worker_loop,
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
                    PoseProcessJob(frame=frame.copy(), csv_path=csv_path, capture_seq=seq)
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
