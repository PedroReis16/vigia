"""Leitura em loop de um ficheiro de vídeo para o FrameBus."""

from __future__ import annotations

import logging
import threading
import time
from pathlib import Path

import cv2  # type: ignore

from worker.frame_bus import FrameBus

logger = logging.getLogger(__name__)


def run_playback(
    video_path: Path,
    bus: FrameBus,
    stop_event: threading.Event,
    *,
    fallback_fps: float = 12.0,
) -> None:
    """Lê o vídeo em loop até ``stop_event``; empurra frames BGR no bus."""
    if not video_path.is_file():
        raise FileNotFoundError(f"Vídeo não encontrado: {video_path}")

    logger.info("Playback a iniciar: %s", video_path)
    while not stop_event.is_set():
        capture = cv2.VideoCapture(str(video_path))
        if not capture.isOpened():
            logger.error("Não foi possível abrir %s", video_path)
            time.sleep(2.0)
            continue

        fps = float(capture.get(cv2.CAP_PROP_FPS) or 0.0)
        if fps < 1.0:
            fps = fallback_fps
        width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
        height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
        if width > 0 and height > 0:
            bus.configure(width, height, fps)

        frame_interval = 1.0 / fps
        try:
            while not stop_event.is_set():
                started = time.monotonic()
                ok, frame = capture.read()
                if not ok or frame is None:
                    break
                bus.push(frame)
                elapsed = time.monotonic() - started
                delay = frame_interval - elapsed
                if delay > 0:
                    stop_event.wait(delay)
        finally:
            capture.release()

        if stop_event.is_set():
            break
        logger.info("Fim do ficheiro — a reiniciar loop: %s", video_path.name)

    logger.info("Playback terminado")
