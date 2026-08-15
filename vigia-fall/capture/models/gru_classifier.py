"""
Classificador GRU binário (ADL vs FALL) baseado em keypoints brutos do YOLO.
"""

from collections import defaultdict, deque

import numpy as np
import onnxruntime as ort

from shared.bundle_paths import repo_or_bundle_root

ALERT_PREDS_FALL = 2
_REQUIRED_JOINTS = [5, 6, 11, 12]  # ombros esquerdo/direito e quadris esquerdo/direito
_LABELS = ["ADL", "FALL"]


class GRUFallClassifier:
    """
    Carrega o modelo GRU .onnx e classifica janelas de 20 frames (T×51 keypoints brutos).
    Mantém histórico por person_id para alertas de queda consecutivos.
    """

    def __init__(self) -> None:
        path = repo_or_bundle_root() / "model" / "gru_2classes.onnx"
        self._session = ort.InferenceSession(
            str(path), providers=["CPUExecutionProvider"]
        )
        self._input_name = self._session.get_inputs()[0].name
        self._history: dict[int, deque] = defaultdict(
            lambda: deque(maxlen=ALERT_PREDS_FALL)
        )

    def predict(self, window: np.ndarray, person_id: int) -> dict | None:
        """
        Recebe janela (T, 51) com keypoints brutos e retorna resultado da classificação.
        Retorna None se a janela não tiver frames válidos suficientes.
        """
        normalized, n_valid = self._normalize_window(window)
        if normalized is None:
            return None

        x = normalized.reshape(1, *normalized.shape).astype(np.float32)
        probs = self._session.run(None, {self._input_name: x})[1][0]
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

    def _normalize_window(self, window: np.ndarray) -> tuple[np.ndarray | None, int]:
        """
        Normalização hip-centered + escala ombro-quadril, idêntica ao treino.
        window: (T, 51) — keypoints YOLO brutos (x, y, conf) por joint.
        Retorna (T, 34) normalizado ou None se frames válidos < 20% da janela.
        """
        T = window.shape[0]
        kp = window.reshape(T, 17, 3)
        kp_xy = kp[:, :, :2].copy()
        kp_conf = kp[:, :, 2]

        valid_frame = np.all(kp_conf[:, _REQUIRED_JOINTS] > 0, axis=1)
        n_valid = int(valid_frame.sum())
        if n_valid < max(1, int(0.2 * T)):
            return None, 0

        joint_valid = kp_conf > 0
        shoulder = kp_xy[:, [5, 6], :].mean(axis=1)  # (T, 2)
        hip = kp_xy[:, [11, 12], :].mean(axis=1)      # (T, 2)
        scale = np.linalg.norm(shoulder - hip, axis=1, keepdims=True) + 1e-6

        normalized = (kp_xy - hip[:, np.newaxis, :]) / scale[:, np.newaxis, :]
        normalized[~joint_valid] = 0.0

        return normalized.reshape(T, 34), n_valid
