"""YOLO model loader and detector with optimized loading and caching."""

import logging
import pickle
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from ultralytics import YOLO
from ultralytics.engine.results import Results

logger = logging.getLogger(__name__)


class YOLODetector:
    """Manages YOLO model loading and inference with lazy initialization."""

    def __init__(self, model_path: str) -> None:
        """Initialize detector with model path.
        
        Args:
            model_path: Path to YOLO model file (relative, absolute, or official model name)
        """
        self._model_path = model_path
        self._model: YOLO | None = None
        self._model_loaded = False

    @property
    def model(self) -> YOLO | None:
        """Lazy load and return the YOLO model."""
        if not self._model_loaded:
            self._model = self._load_model()
            self._model_loaded = True
        return self._model

    def predict(
        self, 
        source: Any, 
        imgsz: int = 640, 
        conf: float = 0.7,
        device: str = "cpu",
        verbose: bool = False,
        **kwargs
    ) -> list[Results] | None:
        """Run YOLO prediction on source.
        
        Args:
            source: Image source (frame, path, etc)
            imgsz: Input image size
            conf: Confidence threshold
            device: Device to run on ('cpu' or 'cuda')
            verbose: Enable verbose output
            **kwargs: Additional YOLO predict parameters
            
        Returns:
            Detection results or None if model not loaded
        """
        if self.model is None:
            logger.warning("Modelo YOLO não carregado, pulando predição")
            return None
        
        return self.model.predict(
            source=source,
            imgsz=imgsz,
            conf=conf,
            device=device,
            verbose=verbose,
            **kwargs
        )

    def _load_model(self) -> YOLO | None:
        """Load YOLO model with path resolution and error handling."""
        model_source = self._resolve_model_path(self._model_path)
        
        try:
            logger.info("Carregando modelo YOLO: %s", model_source)
            return YOLO(model_source)
        except pickle.UnpicklingError as error:
            return self._handle_unpickling_error(error, model_source)
        except FileNotFoundError:
            logger.error(
                "Modelo YOLO não encontrado: %s. Ajuste YOLO_MODEL_PATH para um arquivo existente "
                "(ex.: models/yolov8s-pose.pt) ou para um modelo oficial (ex.: yolov8s-pose.pt).",
                self._model_path,
            )
            return None
        except Exception:
            logger.exception("Falha ao carregar o modelo YOLO: %s", self._model_path)
            return None

    def _resolve_model_path(self, model_path: str) -> str:
        """Resolve model path to absolute path or official model name."""
        configured_model = model_path.strip()
        configured_path = Path(configured_model)

        # If absolute path, use as is
        if configured_path.is_absolute():
            return str(configured_path)
        
        # If contains separators or starts with ., resolve relative to project root
        if any(sep in configured_model for sep in ("/", "\\")) or configured_model.startswith("."):
            project_root = Path(__file__).resolve().parents[2]
            return str((project_root / configured_path).resolve())
        
        # Otherwise, treat as official model name
        return configured_model

    def _handle_unpickling_error(self, error: Exception, model_source: str) -> YOLO | None:
        """Handle unpickling errors by trying weights_only=False mode."""
        if "Weights only load failed" not in str(error):
            logger.exception("Falha ao carregar o modelo YOLO: %s", self._model_path)
            return None

        logger.warning(
            "Falha ao carregar pesos com torch padrão (weights_only=True). "
            "Tentando modo compatível com weights_only=False para fonte confiável: %s",
            self._model_path,
        )

        try:
            with self._compat_torch_load_weights_only_false():
                return YOLO(model_source)
        except FileNotFoundError:
            logger.error(
                "Modelo YOLO não encontrado: %s. Ajuste YOLO_MODEL_PATH para um arquivo existente.",
                self._model_path,
            )
            return None
        except Exception:
            logger.exception("Falha ao carregar o modelo YOLO em modo compatível: %s", self._model_path)
            return None

    @contextmanager
    def _compat_torch_load_weights_only_false(self):
        """Context manager to temporarily set torch.load weights_only=False."""
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
