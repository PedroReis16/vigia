"""Caminhos de recursos em desenvolvimento e no executável PyInstaller (sys._MEIPASS)."""

from __future__ import annotations

import sys
from pathlib import Path


def repo_or_bundle_root() -> Path:
    """Raiz do repositório em dev; pasta de extração do PyInstaller quando congelado."""
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(getattr(sys, "_MEIPASS"))
    # src/app/bundle_paths.py -> parents[2] == raiz do projeto fall-detection
    return Path(__file__).resolve().parents[2]


def classifier_onnx_path() -> Path:
    """ONNX do classificador SVM (empacotado em `model/` no spec)."""
    return repo_or_bundle_root() / "model" / "classifier_svm.onnx"
