""""
Processa os frames capturados para inclusão na fila de processamento
"""

from dataclasses import dataclass
from functools import lru_cache

from ultralytics import YOLO  # pyright: ignore[reportMissingImports]

from models import get_settings

@dataclass(frozen=True)
class YoloModel:
    """
    Modelo YOLO para detecção de poses
    """
    model: YOLO

    @classmethod
    def load(cls) -> "YoloModel":
        """
        Carrega o modelo YOLO
        """
        return cls(model=YOLO(get_settings().yolo_pose_model))

    

@lru_cache
def get_yolo_model() -> YOLO:
    """
    Retorna o modelo YOLO
    """
    return YoloModel.load().model
