import logging
import threading

import cv2

logger = logging.getLogger(__name__)


class WebcamPreviewService:
    def __init__(self, camera_index: int = 0, window_name: str = "older-fall webcam") -> None:
        self._camera_index = camera_index
        self._window_name = window_name
        self._running = False
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        if self._running:
            return

        self._running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        logger.info("Preview da webcam iniciado (camera_index=%s)", self._camera_index)

    def run_blocking(self) -> None:
        if self._running:
            return

        self._running = True
        logger.info(
            "Preview da webcam iniciado em modo bloqueante (camera_index=%s)",
            self._camera_index,
        )
        self._run_loop()

    def stop(self) -> None:
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2)

        cv2.destroyAllWindows()
        logger.info("Preview da webcam finalizado")

    def _run_loop(self) -> None:
        capture = cv2.VideoCapture(self._camera_index)
        if not capture.isOpened():
            logger.warning("Não foi possível abrir a webcam no índice %s", self._camera_index)
            self._running = False
            return

        try:
            while self._running:
                ok, frame = capture.read()
                if not ok:
                    continue

                cv2.imshow(self._window_name, frame)
                key = cv2.waitKey(1) & 0xFF
                if key in (27, ord("q")):
                    self._running = False
                    break
        finally:
            capture.release()
            cv2.destroyAllWindows()
            self._running = False
