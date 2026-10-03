"""
Módulo de integração.

`run_integration` é importado sob demanda para o `__main__` conseguir correr no
Python do host (sem deps do venv) antes de reabrir o .venv.
"""

from __future__ import annotations

from typing import Any

__all__ = ["run_integration"]


def __getattr__(name: str) -> Any:
    if name == "run_integration":
        from .integration_runner import run_integration

        return run_integration
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
