"""Strategy GRU 37: histórico por timestamp + features de pose/movimento + ONNX."""

from __future__ import annotations

from collections import defaultdict, deque

import numpy as np  # type: ignore

from core.models.gru_classifier import GRUFallClassifier
from core.models.pose_features import build_features, valid_from_conf
from core.models.resample import (
    NEIGHBOR_TOLERANCE_S,
    TARGET_FPS,
    WINDOW_FRAMES,
    nearest_indices,
    time_grid,
)
from core.models.types import FallDecision, PoseObservation

GRU_WINDOW_SIZE = WINDOW_FRAMES
GRU_INTERVAL = 0.5
HISTORY_S = 3.0
MIN_VALID_FRAC = 0.20
REQUIRED_JOINTS = [5, 6, 11, 12]


class GruFallClassifier:
    """Pipeline GRU 37 (janela 20 @ 10 fps, inferência a cada 0.5 s)."""

    def __init__(self) -> None:
        self._model = GRUFallClassifier()
        self._history: dict[int, deque] = defaultdict(deque)  # (t, kp17x3)
        self._last_inference: dict[int, float] = {}

    @property
    def window_capacity(self) -> int:
        return GRU_WINDOW_SIZE

    def get_window_fill(self) -> dict[int, tuple[int, int]]:
        return {
            person_id: (len(hist), GRU_WINDOW_SIZE)
            for person_id, hist in self._history.items()
            if len(hist) > 0
        }

    def cleanup(self, active_person_ids: set[int]) -> None:
        for store in (self._history, self._last_inference):
            for pid in [p for p in store if p not in active_person_ids]:
                del store[pid]
        self._model.cleanup(active_person_ids)

    def process(self, observations: list[PoseObservation]) -> list[FallDecision]:
        decisions: list[FallDecision] = []

        for obs in observations:
            kpts = np.asarray(obs.keypoints, dtype=np.float32)
            if kpts.ndim != 2 or kpts.shape[0] < 17:
                continue

            hist = self._history[obs.person_id]
            hist.append((float(obs.timestamp), kpts[:17, :3].copy()))
            while hist and obs.timestamp - hist[0][0] > HISTORY_S:
                hist.popleft()

            last = self._last_inference.get(obs.person_id)
            if last is not None and obs.timestamp - last < GRU_INTERVAL:
                continue

            pred = self._infer(obs.person_id, float(obs.timestamp))
            if pred is None:
                continue

            self._last_inference[obs.person_id] = float(obs.timestamp)
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

    def _infer(self, person_id: int, t_now: float) -> dict | None:
        hist = self._history[person_id]
        window_span = (WINDOW_FRAMES - 1) / TARGET_FPS
        if not hist or t_now - hist[0][0] < window_span - NEIGHBOR_TOLERANCE_S:
            return None

        times = np.array([h[0] for h in hist])
        idx = nearest_indices(times, time_grid(t_now))
        present = idx >= 0
        kp = np.zeros((WINDOW_FRAMES, 17, 3), dtype=np.float32)
        kp[present] = np.stack([hist[i][1] for i in idx[present]])

        frame_valid = np.all(kp[:, REQUIRED_JOINTS, 2] > 0, axis=1)
        n_valid = int(frame_valid.sum())
        if n_valid / WINDOW_FRAMES < MIN_VALID_FRAC:
            self._last_inference[person_id] = t_now
            return None

        feats = build_features(kp[:, :, :2], valid_from_conf(kp[:, :, 2]))
        pred = self._model.predict(feats, person_id)
        if pred is None:
            return None
        pred["n_valid_frames"] = n_valid
        return pred
