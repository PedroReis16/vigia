"""Fase do supervisor de provisionamento (partilhada com o LCD)."""

from __future__ import annotations

import threading

_lock = threading.Lock()
_phase = "idle"
_pairing_stage = "waiting_app"
_cancel: threading.Event | None = None

# Estágios de vínculo (LCD linha 2 durante pairing).
WAITING_APP = "waiting_app"
APP_CONNECTED = "app_connected"
USER_FOUND = "user_found"
WAITING_WIFI = "waiting_wifi"
WIFI_CONNECTING = "wifi_connecting"
WIFI_OK = "wifi_ok"
WIFI_FAIL = "wifi_fail"
PAIRING_ERROR = "pairing_error"


def bind_cancel(event: threading.Event) -> None:
    global _cancel
    _cancel = event


def request_pairing_restart() -> None:
    """Pede ao supervisor para encerrar o beacon e reabrir o pareamento."""
    if _cancel is not None:
        _cancel.set()


def set_phase(phase: str) -> None:
    global _phase, _pairing_stage
    with _lock:
        _phase = phase
        if phase == "pairing":
            _pairing_stage = WAITING_APP


def get_phase() -> str:
    with _lock:
        return _phase


def set_pairing_stage(stage: str) -> None:
    global _pairing_stage
    with _lock:
        _pairing_stage = stage


def get_pairing_stage() -> str:
    with _lock:
        return _pairing_stage
