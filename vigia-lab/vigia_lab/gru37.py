"""GRU de 37 features (nosso) com o mesmo contrato dos classificadores do vigia.

Difere do GRU 34 do vigia em dois pontos de propósito:
- usa `pose_features.build_features` (34 de pose + 3 de velocidade);
- monta a janela de 20 frames numa grade de 10 fps por timestamp, porque o
  modelo foi treinado a 10 fps e as velocidades são por frame.
Alerta, intervalo (0,5 s) e histórico seguem o GRU 34 para comparação justa.
"""

from __future__ import annotations

from collections import defaultdict, deque
from pathlib import Path
from typing import Any

import numpy as np

from core.models.types import FallDecision, PoseObservation
from vigia_lab.pose_features import FEATURE_DIM, build_features, valid_from_conf
from vigia_lab.resample import (
    NEIGHBOR_TOLERANCE_S,
    TARGET_FPS,
    WINDOW_FRAMES,
    nearest_indices,
    time_grid,
)

ALERT_PREDS_FALL = 2
INFERENCE_INTERVAL_S = 0.5
HISTORY_S = 3.0
MIN_VALID_FRAC = 0.20
REQUIRED_JOINTS = [5, 6, 11, 12]
_LABELS = ["ADL", "FALL"]


class Gru37Classifier:
    def __init__(self, onnx_path: str | Path | None = None, session: Any = None) -> None:
        if session is None:
            import onnxruntime as ort

            session = ort.InferenceSession(str(onnx_path), providers=["CPUExecutionProvider"])
        self._session = session
        self._input_name = session.get_inputs()[0].name
        expected = session.get_inputs()[0].shape[-1]
        if expected != FEATURE_DIM:
            raise ValueError(
                f"Modelo espera {expected} features, pose_features fornece {FEATURE_DIM}."
            )
        self._history: dict[int, deque] = defaultdict(deque)  # (t, kp17x3)
        self._last_inference: dict[int, float] = {}
        self._pred_hist: dict[int, deque] = defaultdict(lambda: deque(maxlen=ALERT_PREDS_FALL))

    def cleanup(self, active_person_ids: set[int]) -> None:
        for store in (self._history, self._last_inference, self._pred_hist):
            for pid in [p for p in store if p not in active_person_ids]:
                del store[pid]

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
            if last is not None and obs.timestamp - last < INFERENCE_INTERVAL_S:
                continue
            decision = self._infer(obs.person_id, float(obs.timestamp))
            if decision is not None:
                self._last_inference[obs.person_id] = float(obs.timestamp)
                decisions.append(decision)
        return decisions

    def _infer(self, person_id: int, t_now: float) -> FallDecision | None:
        hist = self._history[person_id]
        window_span = (WINDOW_FRAMES - 1) / TARGET_FPS
        if not hist or t_now - hist[0][0] < window_span - NEIGHBOR_TOLERANCE_S:
            return None  # ainda não há 2,0 s de histórico

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
        x = feats.reshape(1, WINDOW_FRAMES, FEATURE_DIM).astype(np.float32)
        probs = self._session.run(None, {self._input_name: x})[0][0]
        pred = int(np.argmax(probs))

        ph = self._pred_hist[person_id]
        ph.append(pred)
        alert = pred != 0 and len(ph) == ALERT_PREDS_FALL and all(p != 0 for p in ph)
        return FallDecision(
            person_id=person_id,
            label=_LABELS[pred],
            alert=bool(alert),
            detail={
                "probs": [float(p) for p in probs],
                "n_valid_frames": n_valid,
                "oldest_neighbor_age_s": float(t_now - times[idx[present]].min()),
            },
        )
