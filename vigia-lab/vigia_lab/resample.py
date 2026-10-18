"""Reamostragem por TIMESTAMP (nunca por índice de frame).

O GRU 37 foi treinado com janelas de 20 frames a 10 fps (2,0 s). O pipeline do
vigia entrega frames irregulares (~7 a 12 fps). Montar a janela por índice
distorceria as features de velocidade (que são por frame, não por segundo).
"""

from __future__ import annotations

import numpy as np

TARGET_FPS = 10.0
WINDOW_FRAMES = 20
NEIGHBOR_TOLERANCE_S = 0.15


def time_grid(t_end: float, n: int = WINDOW_FRAMES, fps: float = TARGET_FPS) -> np.ndarray:
    """n instantes espaçados de 1/fps terminando em t_end (crescente)."""
    return t_end - (np.arange(n)[::-1] / fps)


def nearest_indices(
    times: np.ndarray, grid: np.ndarray, tolerance: float = NEIGHBOR_TOLERANCE_S
) -> np.ndarray:
    """Para cada instante da grade, o índice do timestamp mais próximo em
    `times` (ordenado), ou -1 se o vizinho estiver além da tolerância."""
    times = np.asarray(times, dtype=np.float64)
    out = np.full(len(grid), -1, dtype=np.int64)
    if times.size == 0:
        return out
    pos = np.searchsorted(times, grid)
    for i, (g, p) in enumerate(zip(grid, pos)):
        candidates = [c for c in (p - 1, p) if 0 <= c < times.size]
        best = min(candidates, key=lambda c: abs(times[c] - g))
        if abs(times[best] - g) <= tolerance:
            out[i] = best
    return out
