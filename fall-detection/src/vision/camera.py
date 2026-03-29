"""Camera manager with optimized opening and fallback support."""

import logging
import platform
from typing import Generator

import cv2
import numpy as np

logger = logging.getLogger(__name__)


class CameraManager:
    """Manages camera capture with fallback support and optimized opening."""

    def __init__(self, camera_indices: list[int], timeout_ms: int = 1000) -> None:
        """Initialize camera manager.
        
        Args:
            camera_indices: List of camera indices to try in order
            timeout_ms: Timeout in milliseconds for camera opening attempts
        """
        self._camera_indices = camera_indices
        self._timeout_ms = timeout_ms
        self._active_camera_index: int | None = None
        self._capture: cv2.VideoCapture | None = None

    @property
    def is_opened(self) -> bool:
        """Check if camera is currently opened."""
        return self._capture is not None and self._capture.isOpened()

    @property
    def active_camera_index(self) -> int | None:
        """Get the currently active camera index."""
        return self._active_camera_index

    def open(self) -> bool:
        """Try to open a camera using configured indices with fallback.
        
        Returns:
            True if a camera was successfully opened, False otherwise
        """
        if self.is_opened:
            logger.warning("Câmera já está aberta")
            return True

        system = platform.system()
        if system == "Windows":
            backends = [cv2.CAP_DSHOW, cv2.CAP_ANY]
        elif system == "Darwin":
            backends = [cv2.CAP_AVFOUNDATION, cv2.CAP_ANY]
        else:
            backends = [cv2.CAP_ANY]

        for idx in self._camera_indices:
            logger.info("Tentando abrir câmera no índice %s...", idx)

            for backend in backends:
                capture = cv2.VideoCapture(idx, backend)

                # Set timeout properties for faster failure detection (when supported)
                capture.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, self._timeout_ms)

                if capture.isOpened():
                    # Verify we can actually read a frame
                    ret, _ = capture.read()
                    if ret:
                        self._capture = capture
                        self._active_camera_index = idx
                        logger.info(
                            "Câmera aberta com sucesso no índice %s (backend=%s)",
                            idx,
                            backend,
                        )
                        return True

                    logger.debug(
                        "Câmera %s abriu mas não consegue ler frames (backend=%s)",
                        idx,
                        backend,
                    )
                    capture.release()

                else:
                    capture.release()
                    logger.debug(
                        "Câmera no índice %s não está disponível (backend=%s)",
                        idx,
                        backend,
                    )
        
        logger.warning(
            "Não foi possível abrir nenhuma câmera nos índices configurados: %s. "
            "Verifique se há uma câmera disponível e ajuste WEBCAM_INDEX no .env.",
            self._camera_indices,
        )
        return False

    def read(self) -> tuple[bool, np.ndarray | None]:
        """Read a frame from the camera.
        
        Returns:
            Tuple of (success, frame) where frame is None if read failed
        """
        if not self.is_opened:
            return False, None
        
        ret, frame = self._capture.read()
        return ret, frame if ret else None

    def release(self) -> None:
        """Release the camera and cleanup resources."""
        if self._capture is not None:
            self._capture.release()
            self._capture = None
            self._active_camera_index = None
            logger.info("Câmera liberada")

    def stream_frames(self, flip_horizontal: bool = False) -> Generator[np.ndarray, None, None]:
        """Generate frames from the camera stream.
        
        Args:
            flip_horizontal: Whether to flip frames horizontally
            
        Yields:
            Camera frames as numpy arrays
        """
        if not self.is_opened:
            logger.error("Câmera não está aberta para streaming")
            return

        while self.is_opened:
            ret, frame = self.read()
            if not ret or frame is None:
                continue
            
            if flip_horizontal:
                frame = cv2.flip(frame, 1)
            
            yield frame

    def __enter__(self):
        """Context manager entry - opens camera."""
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - releases camera."""
        self.release()
