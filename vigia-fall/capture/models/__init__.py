"""
Módulo de modelos utilizados dentro do processo de captura de movimentos
"""

from .yolo_model import get_yolo_model
from .kalman_filter import (
    apply_kalman,
    get_smoothed_scale,
    align_and_store_pca_angle,
)
from .feature_helpers import (
    get_linear_speed,
    get_angular_speed,
    get_trunk_angle,
    get_center_of_mass,
    get_pca_features,
    align_pca_angle,
    get_angle_speed,
    sigmoid_normalize,
    compute_fall_score,
)
from .slider_window import SlidingWindowManager
from .person_runtime import (
    PersonRuntimeStore,
    PersonRuntimeState,
    get_person_runtime_store,
)
from .fall_detector import FallDetector, FallState
from .capture_constants import (
    TRACKED_KPTS,
    MAX_MISSED_FRAMES,
    MIN_KPT_CONF,
    SCALE_EMA_ALPHA,
    MIN_TORSO_SCALE,
    COM_SHOULDER_WEIGHT,
)

__all__ = [
    "get_yolo_model",
    "apply_kalman",
    "get_linear_speed",
    "get_angular_speed",
    "get_trunk_angle",
    "get_center_of_mass",
    "get_pca_features",
    "SlidingWindowManager",
    "PersonRuntimeStore",
    "PersonRuntimeState",
    "get_person_runtime_store",
    "FallDetector",
    "FallState",
    "TRACKED_KPTS",
    "MAX_MISSED_FRAMES",
    "MIN_KPT_CONF",
    "SCALE_EMA_ALPHA",
    "MIN_TORSO_SCALE",
    "COM_SHOULDER_WEIGHT",
    "get_smoothed_scale",
    "align_pca_angle",
    "get_angle_speed",
    "align_and_store_pca_angle",
    "sigmoid_normalize",
    "compute_fall_score",
]
