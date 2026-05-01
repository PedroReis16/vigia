from __future__ import annotations

import cv2

from app.config import Settings, prepare_data_workspace
from app.capture.io import FrameSaveWorker, StreamOutWorker, optional_stream_worker
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

    pose_csv_dir: str | None = None
    if settings.data_path:
        if settings.pose_csv_window_seconds <= 0:
            raise ValueError("pose_csv_window_seconds must be greater than 0")
        prepare_data_workspace(settings, reset=True)
        pose_csv_dir = settings.data_path

    stream: StreamOutWorker | None = None

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

    logger.info("abrindo fonte de vídeo…")
    cap = cv2.VideoCapture(settings.video_capture_source)
    if not cap.isOpened():
        raise RuntimeError(
            f"Não foi possível abrir VIDEO_CAPTURE_SOURCE={settings.video_capture_source!r}. "
            "Experimente outro índice (0, 1, …) ou uma URL válida."
        )
    logger.info("fonte de vídeo OK ({!r}).", settings.video_capture_source)

    logger.info(
        "a carregar modelo YOLO pose (a primeira execução pode descarregar pesos; CPU pode demorar)…"
    )
    pose_model = PoseModel(model_path=settings.yolo_pose_model, device=settings.yolo_model_device)
    logger.info("modelo YOLO pose pronto.")
    show_video = settings.show_video

    run_capture_loop(
        CaptureLoopContext(
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
