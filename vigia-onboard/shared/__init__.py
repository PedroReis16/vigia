"""Código partilhado entre os serviços Python do onboard.

`get_settings` é importado sob demanda para `python -m <módulo>` correr no
Python do host (sem python-dotenv) antes de reabrir o .venv.
"""

from __future__ import annotations

from typing import Any

__all__ = ["get_settings"]


def __getattr__(name: str) -> Any:
    if name == "get_settings":
        from .settings import get_settings

        return get_settings
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
