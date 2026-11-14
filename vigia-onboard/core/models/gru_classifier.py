"""Classificador GRU binário (ADL vs FALL) — ONNX de 37 features."""

from __future__ import annotations

from collections import defaultdict, deque
from pathlib import Path

import numpy as np  # type: ignore
import onnxruntime as ort  # type: ignore

from core.models.pose_features import FEATURE_DIM
from shared.paths import onboard_root

ALERT_PREDS_FALL = 2
_LABELS = ["ADL", "FALL"]
GRU37_ONNX = Path("models") / "gru37" / "gru_v3_f37_candidato.onnx"


def gru37_onnx_path(root: Path | None = None) -> Path:
    """Caminho canónico do ONNX GRU 37 (raiz do onboard ou bundle congelado)."""
    base = root if root is not None else onboard_root()
    return base / GRU37_ONNX


class GRUFallClassifier:
    """Carrega o modelo GRU .onnx e classifica janelas T×37."""

    def __init__(self, onnx_path: str | Path | None = None) -> None:
        path = Path(onnx_path) if onnx_path is not None else gru37_onnx_path()
        self._session = ort.InferenceSession(
            str(path), providers=["CPUExecutionProvider"]
        )
        self._input_name = self._session.get_inputs()[0].name
        expected = self._session.get_inputs()[0].shape[-1]
        if expected != FEATURE_DIM:
            raise ValueError(
                f"Modelo espera {expected} features, pose_features fornece {FEATURE_DIM}."
            )
        self._history: dict[int, deque] = defaultdict(
            lambda: deque(maxlen=ALERT_PREDS_FALL)
        )

    def predict(self, window: np.ndarray, person_id: int) -> dict | None:
        """Classifica janela (T, 37). None se o shape for inválido."""
        if window.ndim != 2 or window.shape[-1] != FEATURE_DIM:
            return None

        x = window.reshape(1, *window.shape).astype(np.float32)
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
            "n_valid_frames": int(window.shape[0]),
        }

    def cleanup(self, active_person_ids: set[int]) -> None:
        stale = [pid for pid in self._history if pid not in active_person_ids]
        for pid in stale:
            del self._history[pid]
