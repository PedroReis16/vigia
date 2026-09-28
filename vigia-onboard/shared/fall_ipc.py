"""IPC de fall_state via EventShmRing (capture/core → integration)."""

from __future__ import annotations

import logging

from shared.event_shm import EventShmRing
from shared.event_types import EVENT_FALL_STATE
from shared.settings import get_settings

logger = logging.getLogger(__name__)

_FALL_STATE_ALIASES: dict[str, str] = {
    "fall": "fall",
    "falling": "fall",
    "normal": "normal",
    "adl": "normal",
    "ok": "normal",
    "suspect": "suspect",
    "false_positive": "false_positive",
    "falsepositive": "false_positive",
}

_fall_shm: EventShmRing | None = None


def normalize_fall_state(label: str) -> str:
    """Mapeia labels dos classificadores para valores canónicos de fall_state."""
    key = (label or "").strip().lower().replace("-", "_").replace(" ", "_")
    return _FALL_STATE_ALIASES.get(key, key or "normal")


def ensure_fall_shm() -> EventShmRing | None:
    """Cria ou anexa o ring de fall_state (writer). None se a SHM falhar."""
    global _fall_shm
    if _fall_shm is not None:
        return _fall_shm
    try:
        _fall_shm = EventShmRing.open_or_create(get_settings().fall_shm_name)
    except Exception as error:
        logger.warning("Fall SHM indisponível: %s", error)
        _fall_shm = None
    return _fall_shm


def attach_fall_shm(shm_name: str | None = None) -> EventShmRing:
    """
    Anexa o ring para leitura no processo de integração.

    Se o ring ainda não existir (integration sobe antes do capture), cria-o
    com o nome canónico para o writer anexar depois.
    """
    name = (shm_name or get_settings().fall_shm_name).strip() or get_settings().fall_shm_name
    return EventShmRing.open_or_create(name)


def enqueue_fall_state(
    label: str,
    *,
    person_id: int = 0,
    capture_ts: float = 0.0,
) -> None:
    """
    Enfileira label de fall_state. No-op se a SHM não puder ser aberta.
    """
    ring = ensure_fall_shm()
    if ring is None:
        logger.info(
            "fall_state=%s person_id=%s (sem SHM)",
            normalize_fall_state(label),
            person_id,
        )
        return
    ring.write(
        EVENT_FALL_STATE,
        normalize_fall_state(label),
        capture_ts=capture_ts,
        person_id=person_id,
    )


def reset_fall_shm_for_tests() -> None:
    """Liberta o singleton (apenas testes)."""
    global _fall_shm
    if _fall_shm is not None:
        _fall_shm.close()
        _fall_shm.unlink()
        _fall_shm = None
