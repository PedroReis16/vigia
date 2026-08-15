"""Fase do supervisor de provisionamento (partilhada com o LCD)."""

from __future__ import annotations

import threading

_lock = threading.Lock()
_phase = "idle"


def set_phase(phase: str) -> None:
    global _phase
    with _lock:
        _phase = phase


def get_phase() -> str:
    with _lock:
        return _phase
