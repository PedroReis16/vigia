"""Testes do EventShmRing e do fall_ipc."""

from __future__ import annotations

import pytest

from shared.event_shm import EventShmRing
from shared.event_types import EVENT_FALL_STATE
from shared.fall_ipc import normalize_fall_state


def test_write_read_PreservaPersonId() -> None:
    ring = EventShmRing.create(slot_count=4, payload_max=64)
    try:
        ring.write(EVENT_FALL_STATE, "normal", capture_ts=1.0, person_id=7)
        event = ring.read_next(timeout=1.0)
        assert event is not None
        assert event.payload == "normal"
        assert event.person_id == 7
        assert event.capture_ts == 1.0
    finally:
        ring.close()
        ring.unlink()


def test_write_FilaCheia_DescartaMaisAntigo() -> None:
    ring = EventShmRing.create(slot_count=2, payload_max=32)
    try:
        ring.write(EVENT_FALL_STATE, "a")
        ring.write(EVENT_FALL_STATE, "b")
        ring.write(EVENT_FALL_STATE, "c")
        first = ring.read_next(timeout=1.0)
        second = ring.read_next(timeout=1.0)
        assert first is not None and first.payload == "b"
        assert second is not None and second.payload == "c"
    finally:
        ring.close()
        ring.unlink()


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("NORMAL", "normal"),
        ("ADL", "normal"),
        ("FALL", "fall"),
        ("SUSPECT", "suspect"),
        ("FALSE_POSITIVE", "false_positive"),
    ],
)
def test_normalize_fall_state(raw: str, expected: str) -> None:
    assert normalize_fall_state(raw) == expected


def test_peek_latest_NaoConsomeAFila() -> None:
    ring = EventShmRing.create(slot_count=4, payload_max=32)
    try:
        ring.write(EVENT_FALL_STATE, "fall")
        peeked = ring.peek_latest()
        assert peeked is not None
        assert peeked.payload == "fall"
        event = ring.read_next(timeout=1.0)
        assert event is not None
        assert event.payload == "fall"
    finally:
        ring.close()
        ring.unlink()
