from __future__ import annotations

import logging
import time
from typing import Any

from .frame_queue import get_frame_queue
from shared import get_settings
import numpy as np # type: ignore
from .models import PoseObservation

logger = logging.getLogger(__name__)


def _create_metadata(results: Any) -> tuple[list[int], list[PoseObservation]] | None:
    """Extração e organização dos pontos do YOLO organizados para cada pessoa detectada"""
    active_ids: list[int] = []
    observations: list[PoseObservation] = []

    for result in results:
        kpts = result.keypoints
        if kpts is None or kpts.data is None or len(kpts.data) <= 0:
            continue

        boxes = result.boxes
        ids_tensor = getattr(boxes, "id", None)
        person_ids = (
            [int(ids_tensor[i].item()) for i in range(len(kpts.data))]
            if ids_tensor is not None and len(ids_tensor) >= len(kpts.data)
            else list(range(len(kpts.data)))
        )

        for person_id, person_kpts in zip(person_ids, kpts.data):
            kpts_np = np.asarray(person_kpts.numpy(), dtype=np.float32)
            if kpts_np.ndim != 2 or kpts_np.shape[1] < 3:
                continue
            if kpts_np.shape[0] < 17:
                padded = np.zeros((17, 3), dtype=np.float32)
                padded[: kpts_np.shape[0]] = kpts_np[:, :3]
                kpts_np = padded
            else:
                kpts_np = kpts_np[:17, :3]

            active_ids.append(person_id)
            observations.append(
                PoseObservation(
                    person_id=person_id,
                    keypoints=kpts_np,
                    timestamp=time.time(),
                )
            )

    return [active_ids, observations]


def save_points(frame_result: np.ndarray) -> None:
    """Salvamento dos pontos capturados pelo YOLO e repasse para o processamento dentro do CORE"""

    settings = get_settings()
    frame_queue = get_frame_queue(settings.frame_rate)
    
    try:
        active_ids, dataset = _create_metadata(frame_result)

    except Exception as error:
        logger.error(f"Erro ao criar o dataset: {error}")
        return


