"""Webcam preview service with YOLO detection - optimized and modular."""

import logging
import threading

import cv2

from src.ml.yolo_detector import YOLODetector
from src.vision.camera import CameraManager
from src.vision.renderer import DetectionRenderer

logger = logging.getLogger(__name__)


class WebcamPreviewService:
    """Service for displaying webcam feed with real-time YOLO detections."""

    def __init__(
        self,
        camera_index: int | list[int] = 0,
        window_name: str = "older-fall webcam",
        flip_horizontal: bool = False,
        yolo_model_path: str = "yolov8s.pt",
        detection_conf: float = 0.7,
        detection_imgsz: int = 640,
    ) -> None:
        """Initialize webcam preview service.
        
        Args:
            camera_index: Camera index or list of indices to try
            window_name: Name for the display window
            flip_horizontal: Whether to flip frames horizontally
            yolo_model_path: Path to YOLO model
            detection_conf: Confidence threshold for detections
            detection_imgsz: Input image size for YOLO
        """
        camera_indices = [camera_index] if isinstance(camera_index, int) else camera_index
        
        self._window_name = window_name
        self._flip_horizontal = flip_horizontal
        self._detection_conf = detection_conf
        self._detection_imgsz = detection_imgsz
        self._running = False
        self._thread: threading.Thread | None = None
        
        # Initialize components (lazy loading)
        self._camera = CameraManager(camera_indices, timeout_ms=1000)
        self._detector = YOLODetector(yolo_model_path)
        self._renderer = DetectionRenderer(show_labels=False, show_conf=False)

    def start(self) -> None:
        """Start webcam preview in background thread."""
        if self._running:
            logger.warning("Preview já está em execução")
            return

        self._running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        logger.info("Preview da webcam iniciado em background")

    def run_blocking(self) -> None:
        """Start webcam preview in blocking mode (current thread)."""
        if self._running:
            logger.warning("Preview já está em execução")
            return

        self._running = True
        logger.info("Preview da webcam iniciado em modo bloqueante")
        self._run_loop()

    def stop(self) -> None:
        """Stop webcam preview and release resources."""
        self._running = False
        
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2)

        self._camera.release()
        cv2.destroyAllWindows()
        logger.info("Preview da webcam finalizado")

    def _run_loop(self) -> None:
        """Main processing loop - simplified and optimized."""
        # Lazy load model (only once)
        if self._detector.model is None:
            logger.error("Falha ao carregar modelo YOLO")
            self._running = False
            return

        # Open camera with fallback
        if not self._camera.open():
            logger.error("Falha ao abrir câmera")
            self._running = False
            return

        logger.info("Loop de detecção iniciado")

        try:
            while self._running:
                # Read frame
                ret, frame = self._camera.read()
                if not ret or frame is None:
                    continue

                # Flip if needed
                if self._flip_horizontal:
                    frame = cv2.flip(frame, 1)

                # Run detection
                results = self._detector.predict(
                    source=frame,
                    imgsz=self._detection_imgsz,
                    conf=self._detection_conf,
                    device="cpu",
                    verbose=False,
                )

                # Render results
                if results:
                    annotated_frame = self._renderer.render(results)
                    if annotated_frame is not None:
                        cv2.imshow(self._window_name, annotated_frame)
                
                # Check for quit key (ESC or 'q')
                key = cv2.waitKey(1) & 0xFF
                if key in (27, ord("q")):
                    logger.info("Tecla de saída pressionada")
                    self._running = False
                    break

        except Exception:
            logger.exception("Erro no loop de detecção")
        finally:
            self._camera.release()
            cv2.destroyAllWindows()
            self._running = False
            logger.info("Loop de detecção finalizado")