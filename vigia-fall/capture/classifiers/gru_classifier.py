"""Strategy GRU: buffer de keypoints crus + ONNX."""

from __future__ import annotations

from collections import defaultdict, deque

import numpy as np

from capture.classifiers.types import FallDecision, PoseObservation
from capture.models.gru_classifier import GRUFallClassifier

GRU_WINDOW_SIZE = 20
GRU_INTERVAL = 0.5
_CONF_MASK = 0.25


class GruFallClassifier:
    """Pipeline GRU (janela 20 frames, inferência a cada 0.5 s)."""

    def __init__(self) -> None:
        self._model = GRUFallClassifier()
        self._buffers: dict[int, deque] = defaultdict(
            lambda: deque(maxlen=GRU_WINDOW_SIZE)
        )
        self._last_inference: dict[int, float] = {}

    def process(self, observations: list[PoseObservation]) -> list[FallDecision]:
        decisions: list[FallDecision] = []

        for obs in observations:
            kpts = np.asarray(obs.keypoints, dtype=np.float32).copy()
            if kpts.ndim != 2 or kpts.shape[0] < 17:
                continue
            kpts = kpts[:17]
            kpts[kpts[:, 2] < _CONF_MASK] = 0.0
            raw = kpts.reshape(-1)  # (51,)

            self._buffers[obs.person_id].append(raw)
            last = self._last_inference.get(obs.person_id)
            if len(self._buffers[obs.person_id]) < GRU_WINDOW_SIZE:
                continue
            if last is not None and (obs.timestamp - last) < GRU_INTERVAL:
                continue

            window = np.array(list(self._buffers[obs.person_id]), dtype=np.float32)
            pred = self._model.predict(window, obs.person_id)
            self._last_inference[obs.person_id] = obs.timestamp
            if pred is None:
                continue

            decisions.append(
                FallDecision(
                    person_id=obs.person_id,
                    label=pred["label"],
                    alert=bool(pred["alert"]),
                    detail={
                        "probs": pred["probs"],
                        "n_valid_frames": pred["n_valid_frames"],
                    },
                )
            )

        return decisions
