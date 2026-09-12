"""Exporta YOLO pose para vigia-fall/models/yolo/ (ONNX, NCNN; CoreML só em macOS).

Uso (a partir de seed-codes/ ou da raiz do repo):
  python export_yolo.py
  YOLO_POSE_MODEL=yolo26s-pose python export_yolo.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

_FALL_ROOT = Path(__file__).resolve().parents[1] / "vigia-fall"
if str(_FALL_ROOT) not in sys.path:
    sys.path.insert(0, str(_FALL_ROOT))

from shared.yolo_export import (  # noqa: E402
    DEFAULT_YOLO_POSE_STEM,
    YoloExportBackend,
    ensure_yolo_pose_export,
)

# Documentação de referência: https://docs.ultralytics.com/pt/modes/export


def main() -> int:
    stem = (os.getenv("YOLO_POSE_MODEL") or DEFAULT_YOLO_POSE_STEM).strip()
    backends: list[YoloExportBackend] = ["onnx", "ncnn"]
    if sys.platform == "darwin":
        backends.append("coreml")
    else:
        print("Aviso: CoreML só é exportado em macOS; a saltar neste host.")

    for backend in backends:
        path = ensure_yolo_pose_export(stem, backend=backend, root=_FALL_ROOT)
        print(f"OK [{backend}]: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
