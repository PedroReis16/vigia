"""Unpack de keypoints YOLO para points brutos (sem imagem)."""

from __future__ import annotations

import time
from typing import Any

import numpy as np  # type: ignore

from core.models.types import PoseObservation


def _as_numpy(value: Any) -> np.ndarray:
    if hasattr(value, "numpy"):
        value = value.numpy()
    return np.asarray(value, dtype=np.float32)


def unpack_raw_points(
    result: Any, timestamp: float | None = None
) -> list[PoseObservation]:
    """
    Copia só person_id + keypoints (17×3) + timestamp a partir do Results YOLO.
    """
    ts = time.time() if timestamp is None else timestamp
    kpts = getattr(result, "keypoints", None)
    data = getattr(kpts, "data", None) if kpts is not None else None
    if data is None or len(data) <= 0:
        return []

    boxes = getattr(result, "boxes", None)
    ids_tensor = getattr(boxes, "id", None) if boxes is not None else None
    person_ids = (
        [int(ids_tensor[i].item() if hasattr(ids_tensor[i], "item") else ids_tensor[i])
         for i in range(len(data))]
        if ids_tensor is not None and len(ids_tensor) >= len(data)
        else list(range(len(data)))
    )

    observations: list[PoseObservation] = []
    for person_id, person_kpts in zip(person_ids, data):
        kpts_np = _as_numpy(person_kpts)
        if kpts_np.ndim != 2 or kpts_np.shape[1] < 3:
            continue
        if kpts_np.shape[0] < 17:
            padded = np.zeros((17, 3), dtype=np.float32)
            padded[: kpts_np.shape[0]] = kpts_np[:, :3]
            kpts_np = padded
        else:
            kpts_np = kpts_np[:17, :3]

        observations.append(
            PoseObservation(
                person_id=int(person_id),
                keypoints=kpts_np,
                timestamp=ts,
            )
        )
    return observations
