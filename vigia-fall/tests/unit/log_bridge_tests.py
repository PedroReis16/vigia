"""Testes do log bridge (emit + drain)."""

from __future__ import annotations

import logging

from shared.event_shm import EventShmRing
from shared.event_types import EVENT_LOG
from shared import log_bridge


def setup_function() -> None:
    log_bridge._log_shm = None  # noqa: SLF001
    log_bridge._dropped_total = 0  # noqa: SLF001


def teardown_function() -> None:
    log_bridge.stop_log_drain()
    log_bridge._log_shm = None  # noqa: SLF001


def test_emit_log_SemInit_FallbackDireto(caplog) -> None:
    logging.getLogger().setLevel(logging.DEBUG)
    with caplog.at_level(logging.INFO, logger="vigia.decision"):
        log_bridge.emit_log(logging.INFO, "state Person 1: NORMAL", capture_ts=1.0)
    assert any("state Person 1: NORMAL [capture_ts=1.000]" in r.message for r in caplog.records)


def test_emit_log_SemInit_NaoEmiteDebugFiltrado(caplog) -> None:
    logging.getLogger().setLevel(logging.INFO)
    with caplog.at_level(logging.DEBUG, logger="vigia.decision"):
        log_bridge.emit_log(logging.DEBUG, "hidden", capture_ts=1.0)
    assert caplog.records == []


def test_emit_e_drain_FormataCaptureTs(caplog) -> None:
    ring = EventShmRing.create(slot_count=8, payload_max=256)
    try:
        log_bridge.init_log_shm(ring.name)
        log_bridge.emit_log(logging.INFO, "state Person 1: FALL ALERT", capture_ts=1234.567)

        with caplog.at_level(logging.INFO, logger="vigia.decision"):
            log_bridge.drain_pending_logs(ring.name, timeout=0.5)

        assert any(
            "state Person 1: FALL ALERT [capture_ts=1234.567]" in r.message
            for r in caplog.records
        )
    finally:
        ring.close()
        ring.unlink()


def test_start_log_drain_ConsomeEventos(caplog) -> None:
    ring = EventShmRing.create(slot_count=8, payload_max=256)
    try:
        logging.getLogger().setLevel(logging.INFO)
        log_bridge.start_log_drain(ring.name)
        ring.write(EVENT_LOG, "state test", level=logging.INFO, capture_ts=1.5)

        import time

        time.sleep(0.05)
        log_bridge.stop_log_drain()

        with caplog.at_level(logging.INFO, logger="vigia.decision"):
            pass
    finally:
        ring.close()
        ring.unlink()


def test_emit_nao_escreve_shm_quando_nivel_filtrado() -> None:
    ring = EventShmRing.create(slot_count=4, payload_max=64)
    try:
        logging.getLogger().setLevel(logging.INFO)
        log_bridge.init_log_shm(ring.name)
        log_bridge.emit_log(logging.DEBUG, "skip me", capture_ts=1.0)
        assert ring.read_next(timeout=0.05) is None
    finally:
        ring.close()
        ring.unlink()
