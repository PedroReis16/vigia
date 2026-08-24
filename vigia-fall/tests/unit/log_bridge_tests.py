"""Testes do log bridge (emit + drain)."""

from __future__ import annotations

import logging

from shared.event_shm import EventShmRing
from shared.event_types import EVENT_LOG
from shared import log_bridge


def setup_function() -> None:
    log_bridge._log_shm = None  # noqa: SLF001


def teardown_function() -> None:
    log_bridge.stop_log_drain()
    log_bridge._log_shm = None  # noqa: SLF001


def test_emit_log_SemInit_NoOp() -> None:
    log_bridge.emit_log(logging.INFO, "hello")


def test_emit_e_drain_FormataCaptureTs(caplog) -> None:
    ring = EventShmRing.create(slot_count=8, payload_max=256)
    try:
        log_bridge.init_log_shm(ring.name)
        log_bridge.emit_log(logging.INFO, "Person 1: FALL ALERT", capture_ts=1234.567)

        with caplog.at_level(logging.INFO, logger="shared.log_bridge"):
            log_bridge.drain_pending_logs(ring.name, timeout=0.5)

        assert any("Person 1: FALL ALERT [capture_ts=1234.567]" in r.message for r in caplog.records)
    finally:
        ring.close()
        ring.unlink()


def test_start_log_drain_ConsomeEventos() -> None:
    ring = EventShmRing.create(slot_count=8, payload_max=256)
    try:
        log_bridge.start_log_drain(ring.name)
        ring.write(EVENT_LOG, "test message", level=logging.INFO, capture_ts=1.5)

        import time

        time.sleep(0.05)
        log_bridge.stop_log_drain()
    finally:
        ring.close()
        ring.unlink()
