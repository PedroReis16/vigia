"""Extração de poses YOLO (partilhada); enriquecimento fica no classificador."""

from __future__ import annotations

import numpy as np

from capture.classifiers.types import PoseObservation
from capture.models import get_person_runtime_store, get_yolo_model
from shared import get_settings


def extract_poses(frame: np.ndarray, capture_date: float) -> list[PoseObservation]:
    """
    Corre YOLO track e devolve keypoints crus (17, 3) por pessoa.
    """
    try:
        settings = get_settings()
        model = get_yolo_model()

        track_result = model.track(
            frame,
            device="cpu",
            conf=0.25,
            verbose=False,
            persist=True,
            tracker=settings.yolo_tracker,
            imgsz=settings.yolo_imgsz,
            classes=[0],
        )

        if not track_result:
            return []

        observations: list[PoseObservation] = []
        active_ids: list[int] = []

        for result in track_result:
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
                        timestamp=capture_date,
                    )
                )

        get_person_runtime_store().cleanup(set(active_ids))
        return observations

    except Exception as error:
        raise RuntimeError(f"Erro ao processar o frame: {error}") from error


def process_frame(frame: np.ndarray, capture_date: float) -> list[PoseObservation]:
    """Alias legado → extract_poses."""
    return extract_poses(frame, capture_date)
