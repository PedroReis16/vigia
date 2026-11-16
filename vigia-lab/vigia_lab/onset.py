"""Início automático da queda a partir da curva do ângulo do tronco. Puro.

Ângulo do tronco = ângulo entre o vetor quadril->ombros e a vertical da imagem
(0° em pé, ~90° deitado). O início é o primeiro instante em que ele passa de
`threshold_deg` por `min_frames` frames válidos consecutivos.

Por que 60° e 2 frames: 60° separa uma inclinação normal (sentar, agachar, varrer
raramente passam de ~45° por mais de um instante) de uma queda; 2 frames evitam
disparar com um único frame de keypoint ruidoso. É referência para medir latência,
não um detector: a marca da operadora continua sendo registrada.
"""

from __future__ import annotations

import numpy as np

TORSO = (5, 6, 11, 12)


def trunk_angle_deg(kp: np.ndarray) -> np.ndarray:
    """kp (T,17,3) -> ângulo (T,) em graus; NaN onde o tronco não é válido."""
    kp = np.asarray(kp, dtype=np.float64)
    ok = (kp[:, list(TORSO), 2] > 0).all(axis=1)
    shoulders = kp[:, [5, 6], :2].mean(axis=1)
    hips = kp[:, [11, 12], :2].mean(axis=1)
    v = shoulders - hips
    ang = np.degrees(np.arctan2(np.abs(v[:, 0]), -v[:, 1]))
    ang[~ok] = np.nan
    return ang


def trunk_onset(
    t_rel: np.ndarray, kp: np.ndarray, threshold_deg: float = 60.0, min_frames: int = 2,
) -> float | None:
    """Primeiro t_rel em que o ângulo passa do limiar por `min_frames` frames válidos seguidos."""
    ang = trunk_angle_deg(kp)
    run = 0
    for i, a in enumerate(ang):
        if np.isfinite(a) and a > threshold_deg:
            run += 1
            if run >= min_frames:
                return float(t_rel[i - min_frames + 1])
        else:
            run = 0
    return None
