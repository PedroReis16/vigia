import logging
import threading

import cv2
from ultralytics import YOLO

logger = logging.getLogger(__name__)


class WebcamPreviewService:
    def __init__(
        self,
        camera_index: int = 0,
        window_name: str = "older-fall webcam",
        flip_horizontal: bool = False,
        yolo_model_path: str = "yolov8s.pt",
    ) -> None:
        self._camera_index = camera_index
        self._window_name = window_name
        self._flip_horizontal = flip_horizontal
        self._yolo_model_path = yolo_model_path
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
        model = YOLO(self._yolo_model_path)

        capture = cv2.VideoCapture(self._camera_index)
        if not capture.isOpened():
            logger.warning("Não foi possível abrir a webcam no índice %s", self._camera_index)
            self._running = False
            return

        try:
            while self._running:
                ret, frame = capture.read()
                if not ret:
                    continue

                if self._flip_horizontal:
                    frame = cv2.flip(frame, 1)

                results = model.predict(
                    source=frame,
                    imgsz=640,
                    conf=0.7,
                    device="cpu",
                    verbose=False,
                )

                result = results[0]
                annotated_frame = result.plot()

                cv2.imshow(self._window_name, annotated_frame)

                key = cv2.waitKey(1) & 0xFF
                if key in (27, ord("q")):
                    self._running = False
                    break
        finally:
            capture.release()
            cv2.destroyAllWindows()
            self._running = False