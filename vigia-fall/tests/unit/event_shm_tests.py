"""Testes do EventShmRing."""

from __future__ import annotations

import logging
import multiprocessing as mp

import pytest

from shared.event_shm import EventShmRing
from shared.event_types import EVENT_FALL_STATE, EVENT_LOG


def test_write_read_PreservaOrdem() -> None:
    ring = EventShmRing.create(slot_count=4, payload_max=64)
    try:
        ring.write(EVENT_FALL_STATE, "normal", capture_ts=1.0)
        ring.write(EVENT_FALL_STATE, "fall", capture_ts=2.0)

        first = ring.read_next(timeout=1.0)
        second = ring.read_next(timeout=1.0)

        assert first is not None
        assert second is not None
        assert first.payload == "normal"
        assert first.capture_ts == 1.0
        assert second.payload == "fall"
        assert second.capture_ts == 2.0
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
        third = ring.read_next(timeout=0.05)

        assert first is not None and first.payload == "b"
        assert second is not None and second.payload == "c"
        assert third is None
    finally:
        ring.close()
        ring.unlink()


def test_reset_InvalidaPendentes() -> None:
    ring = EventShmRing.create(slot_count=4, payload_max=32)
    try:
        ring.write(EVENT_LOG, "msg", level=logging.INFO, capture_ts=3.0)
        ring.reset()
        assert ring.read_next(timeout=0.05) is None
    finally:
        ring.close()
        ring.unlink()


def _spawn_write_event(shm_name: str, label: str) -> None:
    ring = EventShmRing.attach(shm_name)
    ring.write(EVENT_FALL_STATE, label, capture_ts=9.0)
    ring.close()


def test_shm_ComContextoSpawn_PreservaEvento() -> None:
    owner = EventShmRing.create(slot_count=4, payload_max=64)
    try:
        ctx = mp.get_context("spawn")
        proc = ctx.Process(target=_spawn_write_event, args=(owner.name, "fall"))
        proc.start()
        proc.join(timeout=15)
        assert proc.exitcode == 0

        event = owner.read_next(timeout=1.0)
        assert event is not None
        assert event.payload == "fall"
        assert event.capture_ts == 9.0
    finally:
        owner.close()
        owner.unlink()
