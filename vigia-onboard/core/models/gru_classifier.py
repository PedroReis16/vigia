"""Classificador GRU binário (ADL vs FALL) baseado em keypoints brutos."""

from collections import defaultdict, deque

import numpy as np  # type: ignore
import onnxruntime as ort  # type: ignore

from shared.paths import core_root

ALERT_PREDS_FALL = 2
_REQUIRED_JOINTS = [5, 6, 11, 12]
_LABELS = ["ADL", "FALL"]


class GRUFallClassifier:
    """Carrega o modelo GRU .onnx e classifica janelas T×51."""

    def __init__(self) -> None:
        path = core_root() / "models" / "gru_2classes.onnx"
        self._session = ort.InferenceSession(
            str(path), providers=["CPUExecutionProvider"]
        )
        self._input_name = self._session.get_inputs()[0].name
        self._history: dict[int, deque] = defaultdict(
            lambda: deque(maxlen=ALERT_PREDS_FALL)
        )

    def predict(self, window: np.ndarray, person_id: int) -> dict | None:
        """Classifica janela (T, 51). None se frames válidos insuficientes."""
        normalized, n_valid = self._normalize_window(window)
        if normalized is None:
            return None

        x = normalized.reshape(1, *normalized.shape).astype(np.float32)
        probs = self._session.run(None, {self._input_name: x})[0][0]
        label_idx = int(np.argmax(probs))
        label = _LABELS[label_idx]

        self._history[person_id].append(label_idx)
        alert = (
            label_idx != 0
            and len(self._history[person_id]) == ALERT_PREDS_FALL
            and all(p != 0 for p in self._history[person_id])
        )
        return {
            "label": label,
            "probs": probs.tolist(),
            "alert": alert,
            "n_valid_frames": n_valid,
        }

    def cleanup(self, active_person_ids: set[int]) -> None:
        stale = [pid for pid in self._history if pid not in active_person_ids]
        for pid in stale:
            del self._history[pid]

    def _normalize_window(self, window: np.ndarray) -> tuple[np.ndarray | None, int]:
        t_len = window.shape[0]
        kp = window.reshape(t_len, 17, 3)
        kp_xy = kp[:, :, :2].copy()
        kp_conf = kp[:, :, 2]

        valid_frame = np.all(kp_conf[:, _REQUIRED_JOINTS] > 0, axis=1)
        n_valid = int(valid_frame.sum())
        if n_valid < max(1, int(0.2 * t_len)):
            return None, 0

        joint_valid = kp_conf > 0
        shoulder = kp_xy[:, [5, 6], :].mean(axis=1)
        hip = kp_xy[:, [11, 12], :].mean(axis=1)
        scale = np.linalg.norm(shoulder - hip, axis=1, keepdims=True) + 1e-6

        normalized = (kp_xy - hip[:, np.newaxis, :]) / scale[:, np.newaxis, :]
        normalized[~joint_valid] = 0.0

        return normalized.reshape(t_len, 34), n_valid
