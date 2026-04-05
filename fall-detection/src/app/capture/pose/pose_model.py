"""Modelo YOLO pose: rastreia pessoas e extrai keypoints selecionados."""

from __future__ import annotations

import numpy as np
from ultralytics import YOLO

from app.capture.pose.body_data import BodyData
from app.capture.pose.person_data import PersonData


class PoseModel:  # pylint: disable=too-few-public-methods
    """Envolve YOLO pose + track e monta `PersonData` por frame."""

    _TRACKED_KEYPOINTS: tuple[tuple[str, int], ...] = (
        ("nariz", 0),
        ("ombro_esq", 5),
        ("ombro_dir", 6),
    )

    _CONF_MIN: float = 0.75

    def __init__(self, model_path: str, device: str = "cpu") -> None:
        self.model = YOLO(model_path)
        self.device = device

    def _get_person_ids_from_result(self, result, data: np.ndarray) -> list[int]:
        boxes = result.boxes
        ids_tensor = getattr(boxes, "id", None)

        if ids_tensor is not None and len(ids_tensor) >= len(data):
            return [int(ids_tensor[i].item()) for i in range(len(data))]
        return list(range(len(data)))

    def capture_frame(self, frame: np.ndarray) -> list[PersonData]:  # pylint: disable=too-many-locals
        """Roda track no frame e devolve lista de pessoas com keypoints acima do limiar."""
        results = self.model.track(
            frame,
            conf=self._CONF_MIN,
            verbose=False,
            device=self.device,
            persist=True,
        )

        frame_results: list[PersonData] = []

        for result in results:
            kpts = result.keypoints
            if kpts is None or kpts.data is None:
                continue
            data = kpts.data
            if len(data) == 0:
                continue

            person_ids = self._get_person_ids_from_result(result, data)

            for person_id, person in zip(person_ids, data):
                body_data: list[BodyData] = []

                for label, idx in self._TRACKED_KEYPOINTS:
                    x, y, conf = person[idx]
                    cf = float(conf.item())
                    if cf < self._CONF_MIN:
                        continue
                    cx, cy = float(x.item()), float(y.item())
                    body_data.append(BodyData(label, cx, cy, cf))

                frame_results.append(PersonData(person_id, body_data))

        return frame_results
