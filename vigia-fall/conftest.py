"""
Conftest raiz: pré-mocka módulos pesados para testes unitários sem torch/ort completos.
"""

from __future__ import annotations

import sys
from types import ModuleType
from unittest.mock import MagicMock


def _ensure_stub(name: str) -> MagicMock:
    if name not in sys.modules:
        mock = MagicMock()
        mock.__name__ = name
        mock.__package__ = name
        mock.__path__ = []
        sys.modules[name] = mock
    return sys.modules[name]  # type: ignore[return-value]


def _stub_package_tree(*names: str) -> None:
    for name in names:
        parts = name.split(".")
        for i in range(1, len(parts) + 1):
            _ensure_stub(".".join(parts[:i]))


_stub_package_tree(
    "ultralytics",
    "ultralytics.models",
    "ultralytics.utils",
    "torch",
    "torchvision",
    "loguru",
)

if "onnxruntime" not in sys.modules:
    ort = ModuleType("onnxruntime")
    ort.InferenceSession = MagicMock  # type: ignore[attr-defined]
    sys.modules["onnxruntime"] = ort

if "cv2" not in sys.modules:
    cv2 = ModuleType("cv2")
    cv2.VideoCapture = MagicMock  # type: ignore[attr-defined]
    cv2.imencode = MagicMock(return_value=(True, MagicMock()))  # type: ignore[attr-defined]
    sys.modules["cv2"] = cv2
