"""Helpers usados pelo classificador matemático."""

import math

import numpy as np  # type: ignore

from .constants import COM_SHOULDER_WEIGHT


def get_linear_speed(
    current_position: float,
    current_timestamp: float,
    previous_position: float,
    previous_timestamp: float,
) -> float:
    """Velocidade linear a partir da variação de posição no tempo."""
    return (current_position - previous_position) / (
        current_timestamp - previous_timestamp
    )


def get_linear_acceleration(
    current_speed: float,
    current_timestamp: float,
    previous_speed: float,
    previous_timestamp: float,
) -> float:
    """Aceleração linear a partir da variação da velocidade no tempo."""
    return (current_speed - previous_speed) / (
        current_timestamp - previous_timestamp
    )


def get_trunk_angle(
    shoulder_center: tuple[float, float],
    hip_center: tuple[float, float],
) -> float:
    """Ângulo do tronco (rad) em relação ao eixo vertical."""
    shoulder_x, shoulder_y = shoulder_center
    hip_x, hip_y = hip_center
    return math.atan2((hip_x - shoulder_x), (hip_y - shoulder_y))


def get_center_of_mass(
    shoulder_center: tuple[float, float],
    hip_center: tuple[float, float],
    shoulder_weight: float = COM_SHOULDER_WEIGHT,
) -> tuple[float, float]:
    """Centro de massa do tronco como média ponderada ombro/quadril."""
    hip_weight = 1.0 - shoulder_weight
    return (
        shoulder_weight * shoulder_center[0] + hip_weight * hip_center[0],
        shoulder_weight * shoulder_center[1] + hip_weight * hip_center[1],
    )


def get_pca_features(
    coordinates: dict[int, tuple[float, float]],
) -> tuple[float, float]:
    """Razão de eixos e ângulo principal da nuvem de keypoints."""
    points = np.array(list(coordinates.values()), dtype=float)

    if points.shape[0] < 2:
        return 1.0, 0.0

    centered = points - points.mean(axis=0)
    covariance = np.cov(centered, rowvar=False)
    eigenvalues, eigenvectors = np.linalg.eigh(covariance)
    minor_eigenvalue, major_eigenvalue = eigenvalues
    minor_eigenvalue = max(float(minor_eigenvalue), 1e-12)
    aspect_ratio = math.sqrt(float(major_eigenvalue) / minor_eigenvalue)
    principal_axis = eigenvectors[:, -1]
    principal_angle = math.atan2(float(principal_axis[1]), float(principal_axis[0]))
    return aspect_ratio, principal_angle


def align_pca_angle(current_angle: float, previous_angle: float | None) -> float:
    """Remove o flip de sinal do eixo PCA e mantém o ângulo contínuo."""
    if previous_angle is None:
        return current_angle
    candidates = (current_angle, current_angle + math.pi)
    best = min(
        candidates,
        key=lambda a: abs((a - previous_angle + math.pi) % (2 * math.pi) - math.pi),
    )
    return (best + math.pi) % (2 * math.pi) - math.pi


def get_angle_speed(
    current_angle: float,
    current_timestamp: float,
    previous_angle: float,
    previous_timestamp: float,
) -> float:
    """Velocidade angular a partir de ângulos já alinhados."""
    delta = (current_angle - previous_angle + math.pi) % (2 * math.pi) - math.pi
    return delta / (current_timestamp - previous_timestamp)


def sigmoid_normalize(x: float, midpoint: float, steepness: float) -> float:
    """Mapeia x para [0, 1]."""
    return 1 / (1 + math.exp(-steepness * (x - midpoint)))


def compute_fall_score(features: dict[str, float], weights: dict[str, float]) -> float:
    """Score ponderado das features normalizadas."""
    return sum(weights[k] * features[k] for k in features)
