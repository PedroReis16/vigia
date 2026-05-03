"""Tarefas periódicas auxiliares ao processo de streaming (logs / health)."""

from __future__ import annotations

import datetime

from app.logging import get_logger

logger = get_logger("streaming.monitor")


def log_streaming_tick() -> None:
    """Registro periódico de que o ciclo de streaming está ativo."""
    now = datetime.datetime.now()
    logger.debug("monitor streaming ativo ({})", now.isoformat(timespec="seconds"))
