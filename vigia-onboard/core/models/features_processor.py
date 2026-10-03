"""Agregação das features da janela deslizante."""

from typing import Any
import math

import numpy as np  # type: ignore

from .feature_helpers import (
    get_angle_speed,
    get_linear_acceleration,
    get_linear_speed,
    sigmoid_normalize,
)


def __linear_r2(timestamps: np.ndarray, values: np.ndarray) -> float:
    """R² da regressão linear values ~ timestamps."""
    if values.size < 2:
        return 0.0

    slope, intercept = np.polyfit(timestamps, values, 1)
    predicted = slope * timestamps + intercept
    residuals = values - predicted
    ss_res = float(np.sum(residuals**2))
    ss_tot = float(np.sum((values - values.mean()) ** 2))

    if ss_tot <= 1e-12:
        return 1.0 if ss_res <= 1e-12 else 0.0

    return 1.0 - ss_res / ss_tot


def __aggregate_window_features(window_frames: list[dict[str, Any]]) -> dict[str, float]:
    """Agrega a janela num vetor de features de classificação."""
    timestamps: list[float] = []
    trunk_angles: list[float] = []
    pca_ratios: list[float] = []
    com_ys: list[float] = []

    for frame in window_frames:
        trunk_angle = frame.get("trunk_angle")
        pca_ratio = frame.get("pca_ratio")
        center_of_mass = frame.get("center_of_mass")

        if trunk_angle is None or pca_ratio is None or center_of_mass is None:
            continue

        timestamps.append(frame["timestamp"])
        trunk_angles.append(float(trunk_angle))
        pca_ratios.append(float(pca_ratio))
        com_ys.append(float(center_of_mass[1]))

    if len(timestamps) < 2:
        return {
            "trunk_angle_delta": 0.0,
            "trunk_angle_max_rate": 0.0,
            "pca_ratio_delta": 0.0,
            "center_mass_max_accel_y": 0.0,
            "center_mass_accel_poly": 0.0,
            "trunk_angle_trend_r2": 0.0,
        }

    t = np.asarray(timestamps, dtype=float)
    trunk = np.asarray(trunk_angles, dtype=float)
    pca_ratio = np.asarray(pca_ratios, dtype=float)
    com_y = np.asarray(com_ys, dtype=float)
    t_rel = t - t[0]

    trunk_angle_delta = float(trunk[-1] - trunk[0] + math.pi) % (2 * math.pi) - math.pi
    trunk_rates = [
        abs(get_angle_speed(trunk[i], t[i], trunk[i - 1], t[i - 1]))
        for i in range(1, len(trunk))
    ]
    trunk_angle_max_rate = max(trunk_rates) if trunk_rates else 0.0
    pca_ratio_delta = float(pca_ratio[-1] - pca_ratio[0])

    com_speeds_y: list[float] = []
    for i in range(1, len(com_y)):
        com_speeds_y.append(get_linear_speed(com_y[i], t[i], com_y[i - 1], t[i - 1]))

    com_accels_y: list[float] = []
    for i in range(1, len(com_speeds_y)):
        com_accels_y.append(
            get_linear_acceleration(
                com_speeds_y[i],
                t[i + 1],
                com_speeds_y[i - 1],
                t[i],
            )
        )

    center_mass_max_accel_y = max(abs(a) for a in com_accels_y) if com_accels_y else 0.0

    if com_y.size >= 3:
        poly_a, _, _ = np.polyfit(t_rel, com_y, 2)
        center_mass_accel_poly = float(poly_a)
    else:
        center_mass_accel_poly = 0.0

    return {
        "trunk_angle_delta": float(trunk_angle_delta),
        "trunk_angle_max_rate": float(trunk_angle_max_rate),
        "pca_ratio_delta": pca_ratio_delta,
        "center_mass_max_accel_y": float(center_mass_max_accel_y),
        "center_mass_accel_poly": center_mass_accel_poly,
        "trunk_angle_trend_r2": float(__linear_r2(t_rel, trunk)),
    }


def extract_features(window_coordinates: list) -> dict[str, float]:
    """Agrega a janela já normalizada (trunk/CoM/PCA) nas features de score."""
    return __aggregate_window_features(window_coordinates)


def normalize_features(features: dict[str, float]) -> dict[str, float]:
    """Normaliza as features para o intervalo [0, 1]."""
    return {
        "trunk_angle_delta": sigmoid_normalize(
            abs(features["trunk_angle_delta"]), midpoint=0.6, steepness=8
        ),
        "trunk_angle_trend_r2": sigmoid_normalize(
            features["trunk_angle_trend_r2"], midpoint=0.7, steepness=6
        ),
        "pca_ratio_delta": sigmoid_normalize(
            -features["pca_ratio_delta"], midpoint=0.5, steepness=4
        ),
        "center_mass_max_accel_y": sigmoid_normalize(
            features["center_mass_max_accel_y"], midpoint=2.0, steepness=1.5
        ),
        "center_mass_accel_poly": sigmoid_normalize(
            features["center_mass_accel_poly"], midpoint=1.0, steepness=2
        ),
        "trunk_angle_max_rate": sigmoid_normalize(
            features["trunk_angle_max_rate"], midpoint=0.8, steepness=3
        ),
    }
