"""Stubs de deps pesadas para os testes unitários do onboard."""

from __future__ import annotations

import sys
from pathlib import Path
from types import ModuleType
from unittest.mock import MagicMock

_ONBOARD_ROOT = Path(__file__).resolve().parents[1]
_onboard = str(_ONBOARD_ROOT)
if _onboard not in sys.path:
    sys.path.insert(0, _onboard)


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


_stub_package_tree("ultralytics")
_ensure_stub("zmq")
_ensure_stub("cv2")
_ensure_stub("dotenv")

if "onnxruntime" not in sys.modules:
    ort = ModuleType("onnxruntime")
    ort.InferenceSession = MagicMock  # type: ignore[attr-defined]
    sys.modules["onnxruntime"] = ort
