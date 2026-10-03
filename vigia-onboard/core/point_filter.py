"""Filtragem e validação dos points brutos antes da janela por ID."""

from __future__ import annotations

import numpy as np  # type: ignore

from core.models.constants import MIN_KPT_CONF, REQUIRED_JOINTS
from core.models.types import PoseObservation


def filter_observations(
    observations: list[PoseObservation],
) -> list[PoseObservation]:
    """
    Valida o lote e filtra keypoints. Pessoas sem juntas obrigatórias saem.

    Não altera a janela — só devolve o que pode avançar no pipeline.
    """
    filtered: list[PoseObservation] = []
    for obs in observations:
        if not isinstance(obs.person_id, int):
            continue
        kpts = np.asarray(obs.keypoints, dtype=np.float32)
        if kpts.ndim != 2 or kpts.shape[1] < 3:
            continue
        if kpts.shape[0] < 17:
            padded = np.zeros((17, 3), dtype=np.float32)
            padded[: kpts.shape[0]] = kpts[:, :3]
            kpts = padded
        else:
            kpts = kpts[:17, :3].copy()

        kpts[kpts[:, 2] < MIN_KPT_CONF] = 0.0
        if not all(float(kpts[idx, 2]) > 0.0 for idx in REQUIRED_JOINTS):
            continue

        filtered.append(
            PoseObservation(
                person_id=obs.person_id,
                keypoints=kpts,
                timestamp=float(obs.timestamp),
            )
        )
    return filtered
