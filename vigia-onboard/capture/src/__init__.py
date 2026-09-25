"""
Recursos relacionados a captura de imagens.

`run_capture` é importado sob demanda para o bootstrap conseguir correr no
Python do host (sem OpenCV) antes de reabrir o .venv.
"""

from __future__ import annotations

from typing import Any

__all__ = ["run_capture"]


def __getattr__(name: str) -> Any:
    if name == "run_capture":
        from .capture_runner import run_capture

        return run_capture
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
