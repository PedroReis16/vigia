"""
Conftest raiz: pré-mocka módulos pesados para que os testes unitários
possam rodar sem instalar torch/ultralytics/bless/loguru completos.
Carregado antes de tests/conftest.py pelo pytest (rootdir = vigia-fall/).
"""

import sys
from types import ModuleType
from unittest.mock import MagicMock


def _stub(name: str) -> ModuleType:
    mod = ModuleType(name)
    sys.modules[name] = mod
    return mod


def _ensure_stub(name: str) -> MagicMock:
    if name not in sys.modules:
        mock = MagicMock()
        mock.__name__ = name
        mock.__package__ = name
        mock.__path__ = []  # marca como package para submodule access
        sys.modules[name] = mock
    return sys.modules[name]  # type: ignore


def _stub_package_tree(*names: str) -> None:
    """Registra cada nome e todos os ancestrais como MagicMock package."""
    for name in names:
        parts = name.split(".")
        for i in range(1, len(parts) + 1):
            _ensure_stub(".".join(parts[:i]))


# --- Módulos que requerem hardware / instalação pesada ---
_stub_package_tree(
    "ultralytics",
    "ultralytics.models",
    "ultralytics.utils",
    "bless",
    "bless.backends",
    "bless.backends.attribute",
    "bless.backends.characteristic",
    "loguru",
    "torch",
    "torchvision",
)

# cv2: needs a minimal stub so VideoCapture etc. don't crash on import
if "cv2" not in sys.modules:
    _cv2 = _stub("cv2")
    _cv2.VideoCapture = MagicMock
    _cv2.imencode = MagicMock(return_value=(True, MagicMock()))
