""""
Processa os frames capturados para inclusão na fila de processamento
"""

from dataclasses import dataclass
from functools import lru_cache

from ultralytics import YOLO  # pyright: ignore[reportMissingImports]

from shared import get_settings
from shared.bundle_paths import resolve_yolo_pose_weights


@dataclass(frozen=True)
class YoloModel:
    """
    Modelo YOLO para detecção de poses
    """
    model: YOLO

    @classmethod
    def load(cls) -> "YoloModel":
        """
        Carrega o modelo YOLO (preferindo .pt local/bundled quando aplicável)
        """
        weights = resolve_yolo_pose_weights(get_settings().yolo_pose_model)
        return cls(model=YOLO(weights))

    

@lru_cache
def get_yolo_model() -> YOLO:
    """
    Retorna o modelo YOLO
    """
    return YoloModel.load().model
