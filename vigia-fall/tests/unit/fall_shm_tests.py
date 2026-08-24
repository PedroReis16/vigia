"""Testes do IPC de fall_state via SHM."""

from __future__ import annotations

import pytest

from integration import fall_shm
from shared.event_shm import EventShmRing
from shared.event_types import EVENT_FALL_STATE


def setup_function() -> None:
    fall_shm._fall_shm = None  # noqa: SLF001


def teardown_function() -> None:
    fall_shm._fall_shm = None  # noqa: SLF001


def test_enqueue_fall_state_SemInit_NoOp() -> None:
    fall_shm.enqueue_fall_state("fall")


def test_enqueue_fall_state_ComShm_Insere() -> None:
    ring = EventShmRing.create(slot_count=8, payload_max=64)
    try:
        fall_shm.init_fall_shm(ring.name)
        fall_shm.enqueue_fall_state("normal", capture_ts=1.0)
        fall_shm.enqueue_fall_state("fall", capture_ts=2.0)

        first = ring.read_next(timeout=1.0)
        second = ring.read_next(timeout=1.0)
        assert first is not None and first.payload == "normal"
        assert second is not None and second.payload == "fall"
        assert first.event_type == EVENT_FALL_STATE
    finally:
        ring.close()
        ring.unlink()


def test_enqueue_fall_state_FilaCheia_DescartaMaisAntigo() -> None:
    ring = EventShmRing.create(slot_count=2, payload_max=32)
    try:
        fall_shm.init_fall_shm(ring.name)
        fall_shm.enqueue_fall_state("a")
        fall_shm.enqueue_fall_state("b")
        fall_shm.enqueue_fall_state("c")

        first = ring.read_next(timeout=1.0)
        second = ring.read_next(timeout=1.0)
        assert first is not None and first.payload == "b"
        assert second is not None and second.payload == "c"
        assert ring.read_next(timeout=0.05) is None
    finally:
        ring.close()
        ring.unlink()
