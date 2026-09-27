from dataclasses import dataclass
from functools import lru_cache
from typing import Any

import numpy as np # type: ignore

@dataclass(frozen=True)
class PoseObservation:
    """Keypoints YOLO crus de uma pessoa num instante."""

    person_id: int
    keypoints: np.ndarray  # shape (17, 3) — x, y, conf
    timestamp: float

@dataclass(frozen=True)
class FallDecision:
    """Decisão uniforme do miolo de classificação."""

    person_id: int
    label: str
    alert: bool
    detail: dict[str, Any] | None = None


@dataclass(frozen=True)
class CaptureConstants:
    TRACKED_KPTS = {0, 5, 6, 11, 12, 13, 14, 15, 16}
    MAX_MISSED_FRAMES = 15
    MIN_KPT_CONF = 0.25

    # Suavização do scale de normalização (torso)
    SCALE_EMA_ALPHA = 0.1    #peso do frame atual; menor = mais suave; EMA = Media Movel Exponencial
    MIN_TORSO_SCALE = 1e-3   #evita divisão por scale ~0

    # Aproximação biomecânica do CoM do tronco (ombro ↔ quadril)
    # ~0.6 no ombro concentra massa de tronco superior + cabeça; o restante fica no quadril
    COM_SHOULDER_WEIGHT = 0.6

    # trunk_angle = inclinação do tronco
    # center_of_mass = CoM tronco ponderado, normalizado (x, y)
    # pca_ratio = alongmaneto da silhueta
    # pca_angle = orientação do eixo principal (rad)

