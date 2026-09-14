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
_effective_level: int = logging.INFO
_dropped_total: int = 0
_last_drop_warn_ts: float = 0.0

_decision_logger = logging.getLogger("vigia.decision")
_bridge_logger = logging.getLogger(__name__)

_DROP_WARN_INTERVAL_S = 5.0


def _refresh_effective_level() -> None:
    global _effective_level
    root = logging.getLogger()
    _effective_level = root.level or logging.INFO


def should_emit(level: int) -> bool:
    """True se o root logger emitiria este nível."""
    return level >= _effective_level


def init_log_shm(shm_name: str) -> None:
    """Associa o ring de logs no processo capture."""
    global _log_shm
    _refresh_effective_level()
    _log_shm = EventShmRing.attach(shm_name)


def _format_inline(message: str, capture_ts: float) -> str:
    if capture_ts > 0:
        return f"{message} [capture_ts={capture_ts:.3f}]"
    return message


def _emit_to_logger(level: int, text: str) -> None:
    if level >= logging.ERROR:
        _decision_logger.error("%s", text)
    elif level >= logging.WARNING:
        _decision_logger.warning("%s", text)
    elif level >= logging.INFO:
        _decision_logger.info("%s", text)
    else:
        _decision_logger.debug("%s", text)


def _maybe_warn_drop(dropped: int) -> None:
    global _dropped_total, _last_drop_warn_ts
    _dropped_total += dropped
    now = time.monotonic()
    if now - _last_drop_warn_ts < _DROP_WARN_INTERVAL_S:
        return
    _last_drop_warn_ts = now
    _bridge_logger.warning(
        "log_shm: %d evento(s) descartado(s) (total=%d); considere aumentar slot_count",
        dropped,
        _dropped_total,
    )


def emit_log(
    level: int,
    message: str,
    *,
    capture_ts: float = 0.0,
    person_id: int = 0,
) -> None:
    """
    Enfileira mensagem sem I/O no hot path.
    Fallback direto para vigia.decision quando SHM não está inicializada.
    """
    if not should_emit(level):
        return

    text = _format_inline(message, capture_ts)
    if _log_shm is None:
        _emit_to_logger(level, text)
        return

    dropped = _log_shm.write(
        EVENT_LOG,
        message,
        capture_ts=capture_ts,
        person_id=person_id,
        level=level,
    )
    if dropped > 0:
        _maybe_warn_drop(dropped)


def _emit_event(event: EventRecord) -> None:
    if event.event_type != EVENT_LOG:
        return
    _emit_to_logger(event.level, _format_inline(event.payload, event.capture_ts))


def _drain_loop(shm_name: str, stop: threading.Event) -> None:
    ring = EventShmRing.attach(shm_name)
    _refresh_effective_level()
    try:
        while not stop.is_set():
            drained = False
            while True:
                timeout = 0.0 if drained else 0.001
                event = ring.read_next(timeout=timeout)
                if event is None:
                    break
                _emit_event(event)
                drained = True
    finally:
        ring.close()


def start_log_drain(shm_name: str) -> threading.Thread:
    """Inicia thread daemon que drena log SHM para stdout."""
    global _drain_thread, _drain_stop
    _refresh_effective_level()
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
            _emit_event(event)
    finally:
        ring.close()
