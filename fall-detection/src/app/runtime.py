"""Loop principal de captura e exibição."""

from __future__ import annotations

import shutil
import time

import cv2

from app.capture.disk_capture import DiskFrameCapture
from app.capture.roi import central_roi
from app.capture.workers import FrameSaveWorker, optional_stream_worker
from app.config import Settings


def run(settings: Settings) -> None:
    stream = optional_stream_worker(
        settings.stream_ingest_url,
        settings.stream_ingest_token,
        settings.stream_target,
    )

    saver: FrameSaveWorker | None = None
    if settings.frames_dir:
        saver = FrameSaveWorker()
        saver.start()

    disk: DiskFrameCapture | None = None
    if settings.frames_dir:
        disk = DiskFrameCapture(settings.frames_dir, saver)

    cap = cv2.VideoCapture(settings.video_capture_source)

    try:
        if settings.data_path:
            print(f"Removing data path: {settings.data_path}")
            shutil.rmtree(settings.data_path)

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            roi, (x1, y1, x2, y2) = central_roi(frame)

            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

            if disk is not None and settings.capture_interval is not None:
                now = time.monotonic()
                disk.maybe_auto_capture(roi, now, settings.capture_interval)

            if stream is not None:
                stream.send_frame(frame)

            if settings.show_video:
                cv2.imshow("Webcam", frame)
                key = cv2.waitKey(1) & 0xFF
                if key == ord("q"):
                    break

    finally:
        cap.release()
        cv2.destroyAllWindows()
        if stream is not None:
            stream.stop()
        if saver is not None:
            saver.stop()
