"""Strategy GRU: buffer de keypoints crus + ONNX."""

from __future__ import annotations

from collections import defaultdict, deque

import numpy as np  # type: ignore

from core.models.gru_classifier import GRUFallClassifier
from core.models.types import FallDecision, PoseObservation

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

    @property
    def window_capacity(self) -> int:
        return GRU_WINDOW_SIZE

    def get_window_fill(self) -> dict[int, tuple[int, int]]:
        return {
            person_id: (len(buffer), GRU_WINDOW_SIZE)
            for person_id, buffer in self._buffers.items()
            if len(buffer) > 0
        }

    def cleanup(self, active_person_ids: set[int]) -> None:
        stale = [pid for pid in self._buffers if pid not in active_person_ids]
        for pid in stale:
            del self._buffers[pid]
            self._last_inference.pop(pid, None)
        self._model.cleanup(active_person_ids)

    def process(self, observations: list[PoseObservation]) -> list[FallDecision]:
        decisions: list[FallDecision] = []

        for obs in observations:
            kpts = np.asarray(obs.keypoints, dtype=np.float32).copy()
            if kpts.ndim != 2 or kpts.shape[0] < 17:
                continue
            kpts = kpts[:17]
            kpts[kpts[:, 2] < _CONF_MASK] = 0.0
            raw = kpts.reshape(-1)

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
