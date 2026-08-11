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
    Resolve o caminho dos pesos YOLO.

    Se `YOLO_POSE_MODEL` for só o nome (ex.: yolo26s-pose), preferir o ficheiro
    local/bundled `yolo26s-pose.pt` para a placa não depender de download em runtime.
    Caminhos absolutos ou ficheiros existentes passam direto.
    """
    raw = (model_setting or "").strip()
    if not raw:
        raw = "yolo26s-pose"

    candidate = Path(raw)
    if candidate.is_file():
        return str(candidate.resolve())

    root = repo_or_bundle_root()

    if candidate.suffix.lower() == ".pt":
        bundled = root / candidate.name
        if bundled.is_file():
            return str(bundled.resolve())
        return raw

    bundled = root / f"{raw}.pt"
    if bundled.is_file():
        return str(bundled.resolve())

    # Fallback: deixa o Ultralytics resolver/baixar pelo nome (dev local).
    return raw
