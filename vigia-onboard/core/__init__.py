"""Módulo core do onboard."""

from __future__ import annotations

from typing import Any

__all__ = ["run_core"]


def __getattr__(name: str) -> Any:
    if name == "run_core":
        from .runner import run_core

        return run_core
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
