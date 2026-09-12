#!/usr/bin/env python3
"""Garante o export NCNN do YOLO pose em models/yolo/ (pré-requisito do PyInstaller)."""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Permite `python scripts/ensure_yolo_model.py` a partir de vigia-fall/
_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from shared.yolo_export import (  # noqa: E402
    DEFAULT_YOLO_POSE_STEM,
    ensure_yolo_pose_export,
    is_valid_yolo_export_artifact,
    resolve_export_imgsz,
)


def main() -> int:
    stem = (os.getenv("YOLO_POSE_MODEL") or DEFAULT_YOLO_POSE_STEM).strip()
    imgsz = resolve_export_imgsz()
    try:
        path = ensure_yolo_pose_export(
            stem, backend="ncnn", root=_ROOT, imgsz=imgsz
        )
    except Exception as exc:  # noqa: BLE001 — CLI: reportar qualquer falha de export
        print(
            f"ERRO: falha ao garantir export NCNN de {stem!r} (imgsz={imgsz}): {exc}",
            file=sys.stderr,
        )
        return 1

    if not is_valid_yolo_export_artifact(path, "ncnn"):
        print(f"ERRO: artefato NCNN inválido: {path}", file=sys.stderr)
        return 1

    print(f"OK: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
