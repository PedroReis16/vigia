"""Carrega os 3 classificadores e verifica a integridade dos ONNX/pose_features.

O ONNX do GRU 34 NÃO existe no vigia-onboard. Em vez de copiá-lo para dentro do
onboard (sujaria a árvore e o SHA do ficha técnica), apontamos `core_root`
para `vigia-lab/models/gru34` apenas durante a construção do classificador.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from unittest import mock

LAB_ROOT = Path(__file__).resolve().parents[1]
MODELS_DIR = LAB_ROOT / "models"
LOCK_PATH = LAB_ROOT / "models.lock.json"

GRU34_ROOT = MODELS_DIR / "gru34"                       # contém models/gru_2classes.onnx
GRU34_ONNX = GRU34_ROOT / "models" / "gru_2classes.onnx"
GRU37_ONNX = MODELS_DIR / "gru37" / "gru_2classes_v2.onnx"
POSE_FEATURES = Path(__file__).with_name("pose_features.py")

TRACKED = {
    "gru34_onnx": GRU34_ONNX,
    "gru37_onnx": GRU37_ONNX,
    "pose_features_py": POSE_FEATURES,
}


def file_sha256(path: Path) -> str:
    """SHA-256; arquivos .py têm CRLF normalizado (o git do Windows converte)."""
    data = path.read_bytes()
    if path.suffix == ".py":
        data = data.replace(b"\r\n", b"\n")
    return hashlib.sha256(data).hexdigest()


def current_hashes() -> dict[str, str]:
    return {name: file_sha256(p) for name, p in TRACKED.items() if p.is_file()}


def verify_lock(lock_path: Path = LOCK_PATH) -> dict[str, str]:
    """Levanta RuntimeError se algum arquivo faltar ou divergir do lock."""
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    actual = current_hashes()
    problems = []
    for name, expected in lock.items():
        if name not in actual:
            problems.append(f"{name}: arquivo ausente (rode scripts/provision_models.py)")
        elif actual[name] != expected:
            problems.append(f"{name}: hash diverge do models.lock.json")
    if problems:
        raise RuntimeError("; ".join(problems))
    return actual


def build_classifiers(slider_window: int) -> dict[str, object]:
    """Instâncias novas (estado zerado) de GRU34, GRU37 e Math, nesta ordem."""
    from core.classifiers.gru_classifier import GruFallClassifier
    from core.classifiers.math_classifier import MathFallClassifier
    from core.models.person_runtime import get_person_runtime_store
    from vigia_lab.gru37 import Gru37Classifier

    get_person_runtime_store.cache_clear()  # Kalman/FallDetector são singleton global
    with mock.patch("core.models.gru_classifier.core_root", return_value=GRU34_ROOT):
        gru34 = GruFallClassifier()
    return {
        "gru34": gru34,
        "gru37": Gru37Classifier(onnx_path=GRU37_ONNX),
        "math": MathFallClassifier(window_size=slider_window),
    }
