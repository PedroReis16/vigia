from __future__ import annotations

import cv2

from app.config import Settings
from app.capture.loop import CaptureLoopContext, run_capture_loop
from app.capture.pose import PoseModel
from app.fiware.device_sync import (
    load_local_device_settings_required,
)
from app.logging import get_logger

logger = get_logger("capture")


def run_capture(settings: Settings) -> None:
    """Executa o loop de captura de imagens da câmera."""
    load_local_device_settings_required()

    logger.info("abrindo fonte de vídeo…")
    cap = cv2.VideoCapture(settings.video_capture_source)
    if not cap.isOpened():
        raise RuntimeError(
            f"Não foi possível abrir VIDEO_CAPTURE_SOURCE={settings.video_capture_source!r}. "
            "Experimente outro índice (0, 1, …) ou uma URL válida."
        )
    logger.info("fonte de vídeo OK ({!r}).", settings.video_capture_source)

    pose_model = PoseModel(model_path=settings.yolo_pose_model)
    logger.info("modelo YOLO pose pronto.")
    show_video = settings.show_video

    run_capture_loop(
        CaptureLoopContext(
            cap=cap,
            show_video=show_video,
            pose_model=pose_model
        )
    )
