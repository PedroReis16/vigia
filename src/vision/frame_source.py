"""Abstração de fonte de frames para preview: câmera ao vivo ou arquivo de vídeo (modo debug)."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Protocol

import cv2
import numpy as np

from src.vision.camera import CameraManager

logger = logging.getLogger(__name__)


class FrameSource(Protocol):
    """Protocolo para qualquer fonte de frames (câmera ou vídeo)."""

    def open(self) -> bool:
        """Abre a fonte. Retorna True se sucesso."""
        ...

    def read(self) -> tuple[bool, np.ndarray | None]:
        """Lê um frame. Retorna (sucesso, frame). Frame é None se falhou."""
        ...

    def release(self) -> None:
        """Libera recursos."""
        ...

    @property
    def is_opened(self) -> bool:
        """Indica se a fonte está aberta."""
        ...


class VideoFileFrameSource:
    """Fonte de frames a partir de um arquivo de vídeo (modo debug)."""

    def __init__(
        self,
        video_path: str | Path,
        *,
        loop: bool = True,
    ) -> None:
        """Inicializa a fonte de vídeo.

        Args:
            video_path: Caminho para o arquivo de vídeo (.mp4, .avi, etc.).
            loop: Se True, ao chegar ao fim do vídeo reinicia do início (útil para debug).
        """
        self._video_path = Path(video_path)
        self._loop = loop
        self._capture: cv2.VideoCapture | None = None

    @property
    def is_opened(self) -> bool:
        return self._capture is not None and self._capture.isOpened()

    def open(self) -> bool:
        if self.is_opened:
            logger.warning("Vídeo já está aberto")
            return True

        if not self._video_path.exists():
            logger.error("Arquivo de vídeo não encontrado: %s", self._video_path)
            return False

        self._capture = cv2.VideoCapture(str(self._video_path))
        if not self._capture.isOpened():
            logger.error("Não foi possível abrir o vídeo: %s", self._video_path)
            self._capture = None
            return False

        logger.info("Modo debug: vídeo aberto %s (loop=%s)", self._video_path, self._loop)
        return True

    def read(self) -> tuple[bool, np.ndarray | None]:
        if not self.is_opened:
            return False, None

        ret, frame = self._capture.read()
        if ret and frame is not None:
            return True, frame

        if self._loop and self._capture is not None:
            self._capture.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ret, frame = self._capture.read()
            return ret, frame if ret else None

        return False, None

    def release(self) -> None:
        if self._capture is not None:
            self._capture.release()
            self._capture = None
            logger.info("Vídeo liberado: %s", self._video_path)


def create_frame_source(
    camera_indices: list[int],
    video_path: str | Path | None = None,
    *,
    camera_timeout_ms: int = 1000,
    video_loop: bool = True,
) -> CameraManager | VideoFileFrameSource:
    """Cria a fonte de frames (câmera ou vídeo) conforme configuração.

    Args:
        camera_indices: Índices de câmera a tentar (usado se video_path for None).
        video_path: Se informado, usa arquivo de vídeo em vez da câmera.
        camera_timeout_ms: Timeout ao abrir câmera.
        video_loop: Se True, vídeo reinicia do início ao terminar.

    Returns:
        Instância de CameraManager ou VideoFileFrameSource.
    """
    if video_path is not None:
        return VideoFileFrameSource(video_path, loop=video_loop)
    return CameraManager(camera_indices, timeout_ms=camera_timeout_ms)
