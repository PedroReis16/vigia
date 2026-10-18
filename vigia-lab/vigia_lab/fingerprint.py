"""Ficha técnica reprodutível de uma sessão/tomada (resposta à crítica de fidelidade)."""

from __future__ import annotations

import hashlib
import platform
import subprocess
import sys
from pathlib import Path
from typing import Any

from vigia_lab import __version__, bootstrap
from vigia_lab.models_gru import current_hashes


def _git(*args: str) -> str:
    try:
        out = subprocess.run(
            ["git", *args], cwd=bootstrap.ONBOARD_ROOT, capture_output=True, text=True, timeout=10,
        )
        return out.stdout.strip() if out.returncode == 0 else ""
    except (OSError, subprocess.SubprocessError):
        return ""


def git_state() -> dict[str, Any]:
    sha = _git("rev-parse", "HEAD")
    dirty = _git("status", "--porcelain", "--", ".")
    return {
        "onboard_commit": sha or None,
        "onboard_tree_dirty": bool(dirty),
        "onboard_dirty_files": dirty.splitlines()[:20],
    }


def _version(name: str) -> str | None:
    try:
        from importlib.metadata import version

        return version(name)
    except Exception:
        return None


def file_sha256(path: Path) -> str | None:
    if not path.is_file():
        return None
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def build_fingerprint(
    *, stream_kwargs: dict[str, Any], yolo_weights: Path | None, predictor_args: dict[str, Any] | None,
    settings: Any, imgsz_onnx: Any = None,
) -> dict[str, Any]:
    from vigia_lab.pose_features import FEATURES_VERSION

    return {
        "vigia_lab_version": __version__,
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "processor": platform.processor(),
        "versions": {n: _version(n) for n in ("ultralytics", "onnxruntime", "opencv-python", "numpy", "torch")},
        "pose_model": {
            "name": getattr(settings, "yolo_model", None),
            "file": str(yolo_weights) if yolo_weights else None,
            "sha256": file_sha256(yolo_weights) if yolo_weights else None,
            "imgsz_onnx": imgsz_onnx,
        },
        "stream_kwargs": stream_kwargs,
        "effective_predictor_args": predictor_args,
        "settings": {
            "frame_rate": getattr(settings, "frame_rate", None),
            "slider_window_size": getattr(settings, "slider_window_size", None),
        },
        "models_sha256": current_hashes(),
        "features_version": FEATURES_VERSION,
        **git_state(),
    }
