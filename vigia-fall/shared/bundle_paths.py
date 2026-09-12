"""Caminhos de recursos em desenvolvimento e no executável PyInstaller (sys._MEIPASS)."""

from __future__ import annotations

import sys
from pathlib import Path


def repo_or_bundle_root() -> Path:
    """Raiz do projeto em dev; pasta de extração do PyInstaller quando congelado."""
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(getattr(sys, "_MEIPASS"))
    # shared/bundle_paths.py -> parents[1] == raiz de vigia-fall
    return Path(__file__).resolve().parents[1]


def resolve_yolo_pose_weights(model_setting: str) -> str:
    """
    Resolve o path do modelo YOLO pose exportado (ONNX / CoreML / NCNN).

    Delega para ``shared.yolo_export.ensure_yolo_pose_export`` (export on-demand em
    dev; só resolução no bundle congelado).
    """
    # Import local evita ciclo: yolo_export importa repo_or_bundle_root daqui.
    from shared.yolo_export import ensure_yolo_pose_export

    return str(ensure_yolo_pose_export(model_setting))
