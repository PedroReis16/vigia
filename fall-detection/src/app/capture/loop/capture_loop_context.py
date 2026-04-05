"""Parâmetros e dependências do loop principal de captura."""

from __future__ import annotations

from dataclasses import dataclass

import cv2

from app.capture.io.frame_save_worker import FrameSaveWorker
from app.capture.io.stream_out_worker import StreamOutWorker
from app.capture.pose.pose_model import PoseModel


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
