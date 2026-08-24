"""
Bridge de logs: capture escreve eventos em SHM; supervisor drena para stdout.
"""

from __future__ import annotations

import logging
import threading
import time

from shared.event_shm import EventRecord, EventShmRing
from shared.event_types import EVENT_LOG

_log_shm: EventShmRing | None = None
_drain_thread: threading.Thread | None = None
_drain_stop: threading.Event | None = None
_logger = logging.getLogger(__name__)

_LEVEL_NAMES = {
    logging.DEBUG: "debug",
    logging.INFO: "info",
    logging.WARNING: "warning",
    logging.ERROR: "error",
}


def init_log_shm(shm_name: str) -> None:
    """Associa o ring de logs no processo capture."""
    global _log_shm
    _log_shm = EventShmRing.attach(shm_name)


def emit_log(
    level: int,
    message: str,
    *,
    capture_ts: float = 0.0,
    person_id: int = 0,
) -> None:
    """Enfileira mensagem de log sem I/O. No-op se SHM não inicializada."""
    if _log_shm is None:
        return
    _log_shm.write(
        EVENT_LOG,
        message,
        capture_ts=capture_ts,
        person_id=person_id,
        level=level,
    )


def _format_event(event: EventRecord) -> str:
    if event.capture_ts > 0:
        return f"{event.payload} [capture_ts={event.capture_ts:.3f}]"
    return event.payload


def _drain_loop(shm_name: str, stop: threading.Event) -> None:
    ring = EventShmRing.attach(shm_name)
    try:
        while not stop.is_set():
            event = ring.read_next(timeout=0.001)
            if event is None:
                continue
            if event.event_type != EVENT_LOG:
                continue
            text = _format_event(event)
            if event.level >= logging.ERROR:
                _logger.error("%s", text)
            elif event.level >= logging.WARNING:
                _logger.warning("%s", text)
            elif event.level >= logging.INFO:
                _logger.info("%s", text)
            else:
                _logger.debug("%s", text)
    finally:
        ring.close()


def start_log_drain(shm_name: str) -> threading.Thread:
    """Inicia thread daemon que drena log SHM para stdout."""
    global _drain_thread, _drain_stop
    stop = threading.Event()
    thread = threading.Thread(
        target=_drain_loop,
        args=(shm_name, stop),
        name="log-drain",
        daemon=True,
    )
    _drain_stop = stop
    _drain_thread = thread
    thread.start()
    return thread


def stop_log_drain(timeout: float = 1.0) -> None:
    """Para o drain e aguarda thread finalizar."""
    global _drain_thread, _drain_stop
    if _drain_stop is not None:
        _drain_stop.set()
    if _drain_thread is not None:
        _drain_thread.join(timeout=timeout)
    _drain_thread = None
    _drain_stop = None


def drain_pending_logs(shm_name: str, timeout: float = 0.5) -> None:
    """Drena eventos restantes (ex.: shutdown)."""
    ring = EventShmRing.attach(shm_name)
    try:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            event = ring.read_next(timeout=0.01)
            if event is None:
                break
            if event.event_type != EVENT_LOG:
                continue
            text = _format_event(event)
            _logger.info("%s", text)
    finally:
        ring.close()
