"""Parâmetros e dependências do loop principal de captura."""

from __future__ import annotations

from dataclasses import dataclass

import cv2

from app.capture.pose.pose_model import PoseModel


@dataclass
class CaptureLoopContext:
    cap: cv2.VideoCapture
    show_video: bool
    pose_model: PoseModel
