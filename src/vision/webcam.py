import logging
import pickle
import threading
from contextlib import contextmanager
from pathlib import Path

import cv2
from ultralytics import YOLO

logger = logging.getLogger(__name__)


class WebcamPreviewService:
    def __init__(
        self,
        camera_index: int | list[int] = 0,
        window_name: str = "older-fall webcam",
        flip_horizontal: bool = False,
        yolo_model_path: str = "yolov8s.pt",
    ) -> None:
        self._camera_indices = [camera_index] if isinstance(camera_index, int) else camera_index
        self._active_camera_index: int | None = None
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
        logger.info("Preview da webcam iniciado (camera_indices=%s)", self._camera_indices)

    def run_blocking(self) -> None:
        if self._running:
            return

        self._running = True
        logger.info(
            "Preview da webcam iniciado em modo bloqueante (camera_indices=%s)",
            self._camera_indices,
        )
        self._run_loop()

    def stop(self) -> None:
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2)

        cv2.destroyAllWindows()
        logger.info("Preview da webcam finalizado")

    def _load_model(self) -> YOLO | None:
        configured_model = self._yolo_model_path.strip()
        project_root = Path(__file__).resolve().parents[2]

        model_source = configured_model
        configured_path = Path(configured_model)

        if configured_path.is_absolute():
            model_source = str(configured_path)
        elif any(separator in configured_model for separator in ("/", "\\")) or configured_model.startswith("."):
            model_source = str((project_root / configured_path).resolve())

        try:
            return YOLO(model_source)
        except pickle.UnpicklingError as error:
            if "Weights only load failed" not in str(error):
                logger.exception("Falha ao carregar o modelo YOLO: %s", self._yolo_model_path)
                return None

            logger.warning(
                "Falha ao carregar pesos com torch padrão (weights_only=True). "
                "Tentando modo compatível com weights_only=False para fonte confiável: %s",
                self._yolo_model_path,
            )

            try:
                with self._compat_torch_load_weights_only_false():
                    return YOLO(model_source)
            except FileNotFoundError:
                logger.error(
                    "Modelo YOLO não encontrado: %s. Ajuste YOLO_MODEL_PATH para um arquivo existente "
                    "(ex.: models/yolo26s-pose.pt) ou para um modelo oficial (ex.: yolov8s-pose.pt).",
                    self._yolo_model_path,
                )
                return None
            except Exception:
                logger.exception("Falha ao carregar o modelo YOLO em modo compatível: %s", self._yolo_model_path)
                return None
        except FileNotFoundError:
            logger.error(
                "Modelo YOLO não encontrado: %s. Ajuste YOLO_MODEL_PATH para um arquivo existente "
                "(ex.: models/yolo26s-pose.pt) ou para um modelo oficial (ex.: yolov8s-pose.pt).",
                self._yolo_model_path,
            )
            return None
        except Exception:
            logger.exception("Falha ao carregar o modelo YOLO: %s", self._yolo_model_path)
            return None

    @contextmanager
    def _compat_torch_load_weights_only_false(self):
        import torch

        original_torch_load = torch.load

        def _compat_torch_load(*args, **kwargs):
            kwargs.setdefault("weights_only", False)
            return original_torch_load(*args, **kwargs)

        torch.load = _compat_torch_load
        try:
            yield
        finally:
            torch.load = original_torch_load

    def _open_camera(self) -> cv2.VideoCapture | None:
        """Tenta abrir a câmera usando os índices configurados, com fallback automático."""
        for idx in self._camera_indices:
            logger.info("Tentando abrir câmera no índice %s...", idx)
            capture = cv2.VideoCapture(idx)
            if capture.isOpened():
                self._active_camera_index = idx
                logger.info("Câmera aberta com sucesso no índice %s", idx)
                return capture
            capture.release()
            logger.debug("Câmera no índice %s não está disponível", idx)
        
        logger.warning(
            "Não foi possível abrir nenhuma câmera nos índices configurados: %s. "
            "Verifique se há uma câmera disponível e ajuste WEBCAM_INDEX no .env.",
            self._camera_indices,
        )
        return None

    def _run_loop(self) -> None:
        model = self._load_model()
        if model is None:
            self._running = False
            return

        capture = self._open_camera()
        if capture is None:
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