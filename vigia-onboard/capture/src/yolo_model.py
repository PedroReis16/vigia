"""Carrega o YOLO pose exportado para a plataforma atual."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

from ultralytics import YOLO  # pyright: ignore[reportMissingImports]

from .settings import get_settings
from .yolo_export import ensure_yolo_pose_export


@dataclass(frozen=True)
class YoloModel:
    """Modelo YOLO para detecção de poses."""

    model: YOLO

    @classmethod
    def load(cls) -> YoloModel:
        """
        Carrega o modelo YOLO pose exportado para a plataforma atual
        (ONNX / CoreML / NCNN), exportando on-demand em desenvolvimento.
        """
        weights = ensure_yolo_pose_export(get_settings().yolo_model)
        return cls(model=YOLO(str(weights)))


@lru_cache
def get_yolo_model() -> YOLO:
    """Retorna o modelo YOLO (singleton)."""
    return YoloModel.load().model
