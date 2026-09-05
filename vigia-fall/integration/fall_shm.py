"""
IPC de fall_state via EventShmRing (shared memory).
"""

from __future__ import annotations

from shared.event_shm import EventShmRing
from shared.event_types import EVENT_FALL_STATE

_fall_shm: EventShmRing | None = None


def init_fall_shm(shm_name: str) -> None:
    """Associa o ring de fall_state no processo filho."""
    global _fall_shm
    _fall_shm = EventShmRing.attach(shm_name)


def enqueue_fall_state(label: str, *, capture_ts: float = 0.0) -> None:
    """
    Enfileira label de fall_state. No-op se SHM não inicializada (captura standalone).
    """
    if _fall_shm is None:
        return
    _fall_shm.write(EVENT_FALL_STATE, label, capture_ts=capture_ts)


def attach_fall_shm(shm_name: str) -> EventShmRing:
    """Anexa o ring para leitura no processo FIWARE."""
    return EventShmRing.attach(shm_name)
