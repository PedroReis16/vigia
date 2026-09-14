"""
Processa os frames capturados para inclusão na fila de processamento
"""

from dataclasses import dataclass
from functools import lru_cache

from ultralytics import YOLO  # pyright: ignore[reportMissingImports]

from shared import get_settings
from shared.yolo_export import ensure_yolo_pose_export


@dataclass(frozen=True)
class YoloModel:
    """
    Modelo YOLO para detecção de poses
    """
    model: YOLO

    @classmethod
    def load(cls) -> "YoloModel":
        """
        Carrega o modelo YOLO pose exportado para a plataforma atual
        (ONNX / CoreML / NCNN), exportando on-demand em desenvolvimento.
        """
        weights = ensure_yolo_pose_export(get_settings().yolo_pose_model)
        return cls(model=YOLO(str(weights)))


@lru_cache
def get_yolo_model() -> YOLO:
    """
    Retorna o modelo YOLO
    """
    return YoloModel.load().model
