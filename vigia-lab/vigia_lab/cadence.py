"""Simulação da cadência de pose do dispositivo (ANTES do YOLO).

O vídeo foi gravado a ~30 fps, mas a Raspberry processa menos frames por segundo.
`pose_fps` é a taxa MÉDIA de frames processados: os instantes-alvo são t0, t0+1/pose_fps, ...
e para cada alvo escolhe-se o frame de vídeo mais próximo (no máximo meio intervalo de câmera
de erro). Isso importa porque o tracker (BoT-SORT) só vê esses frames: com poucos frames ele
perde a pessoa mais fácil durante a queda, e alimentá-lo a 30 fps esconderia esse defeito.

Por que grade de tempo-alvo e não "1/pose_fps depois do último": com o jitter de ~0,1 ms dos
timestamps, a regra "pelo menos 1/pose_fps depois" arredondaria para baixo em ~25% dos casos
(3 frames = 99,9 ms < 100 ms) e entregaria ~9 fps quando se pediu 10.
"""

from __future__ import annotations

import numpy as np

_EPS = 1e-9


def select_frames(times: np.ndarray, pose_fps: float) -> np.ndarray:
    """Índices dos frames que o dispositivo processaria. `times` em segundos, crescente."""
    if pose_fps <= 0:
        raise ValueError("pose_fps deve ser positivo")
    t = np.asarray(times, dtype=np.float64)
    if len(t) == 0:
        return np.array([], dtype=np.int64)
    period = 1.0 / pose_fps
    keep = [0]
    next_target = t[0] + period
    for i in range(1, len(t)):
        half_gap = (t[i] - t[i - 1]) / 2.0
        if t[i] >= next_target - half_gap - _EPS:
            keep.append(i)
            next_target += period
            while next_target - half_gap <= t[i] + _EPS:      # câmera/processamento atrasou: pula alvos perdidos
                next_target += period
    return np.array(keep, dtype=np.int64)
