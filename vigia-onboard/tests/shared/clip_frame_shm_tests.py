"""Testes do ClipFrameRing (janela deslizante)."""

from __future__ import annotations

import os

import numpy as np

from shared.clip_frame_shm import ClipFrameRing


def test_push_snapshot_OrdemAntigoParaRecente() -> None:
    ring = ClipFrameRing.create(slot_count=3, max_payload=64)
    try:
        for value in (1, 2, 3):
            frame = np.full((2, 2, 3), value, dtype=np.uint8)
            assert ring.push(frame, capture_ts=float(value)) is True

        snap = ring.snapshot()
        assert len(snap) == 3
        assert [int(item.frame[0, 0, 0]) for item in snap] == [1, 2, 3]
        assert [item.capture_ts for item in snap] == [1.0, 2.0, 3.0]
    finally:
        ring.close()
        ring.unlink()


def test_push_DropOldestQuandoCheio() -> None:
    ring = ClipFrameRing.create(slot_count=2, max_payload=64)
    try:
        for value in (1, 2, 3):
            ring.push(np.full((2, 2, 3), value, dtype=np.uint8), capture_ts=float(value))

        snap = ring.snapshot()
        assert len(snap) == 2
        assert [int(item.frame[0, 0, 0]) for item in snap] == [2, 3]
    finally:
        ring.close()
        ring.unlink()


def test_push_MaiorQueBuffer_RetornaFalse() -> None:
    ring = ClipFrameRing.create(slot_count=2, max_payload=8)
    try:
        assert ring.push(np.zeros((4, 4, 3), dtype=np.uint8)) is False
        assert len(ring) == 0
    finally:
        ring.close()
        ring.unlink()


def test_open_or_create_RecriaQuandoSlotsDiferem() -> None:
    name = f"vigia-clip-{os.getpid()}"
    small = ClipFrameRing.create(slot_count=2, max_payload=64, name=name)
    small.close()
    ring = ClipFrameRing.open_or_create(name, slot_count=4, max_payload=64)
    try:
        assert ring.slot_count == 4
        assert ring.push(np.zeros((2, 2, 3), dtype=np.uint8)) is True
    finally:
        ring.close()
        ring.unlink()


def test_reset_LimpaJanela() -> None:
    ring = ClipFrameRing.create(slot_count=2, max_payload=64)
    try:
        ring.push(np.ones((2, 2, 3), dtype=np.uint8), capture_ts=1.0)
        ring.reset()
        assert ring.snapshot() == []
        assert len(ring) == 0
    finally:
        ring.close()
        ring.unlink()
