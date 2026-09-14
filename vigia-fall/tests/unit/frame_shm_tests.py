"""Testes unitários para shared memory de frames."""

from __future__ import annotations

import multiprocessing as mp

import numpy as np

from streaming.frame_shm import DEFAULT_MAX_PAYLOAD, FrameShmRing


def test_write_read_PreservaConteudoBGR() -> None:
    ring = FrameShmRing.create(max_payload=64)
    try:
        original = np.arange(12, dtype=np.uint8).reshape(2, 2, 3)
        assert ring.write(original, 30) is True

        item = ring.read_latest(timeout=1.0)
        assert item is not None
        np.testing.assert_array_equal(item.frame, original)
        assert item.stream_fps == 30
    finally:
        ring.close()
        ring.unlink()


def test_write_VazioOuNone_RetornaFalse() -> None:
    ring = FrameShmRing.create(max_payload=64)
    try:
        assert ring.write(None, 30) is False  # type: ignore[arg-type]
        assert ring.write(np.array([], dtype=np.uint8), 30) is False
        assert ring.read_latest(timeout=0.05) is None
    finally:
        ring.close()
        ring.unlink()


def test_write_SobrescreveUltimoFrame() -> None:
    ring = FrameShmRing.create(max_payload=64)
    try:
        first = np.zeros((2, 2, 3), dtype=np.uint8)
        second = np.ones((2, 2, 3), dtype=np.uint8)
        ring.write(first, 30)
        ring.read_latest(timeout=1.0)
        ring.write(second, 30)

        item = ring.read_latest(timeout=1.0)
        assert item is not None
        np.testing.assert_array_equal(item.frame, second)
    finally:
        ring.close()
        ring.unlink()


def test_write_MaiorQueBuffer_RetornaFalse() -> None:
    ring = FrameShmRing.create(max_payload=8)
    try:
        huge = np.zeros((4, 4, 3), dtype=np.uint8)
        assert ring.write(huge, 30) is False
    finally:
        ring.close()
        ring.unlink()


def test_reset_sequence_InvalidaLeitura() -> None:
    ring = FrameShmRing.create(max_payload=64)
    try:
        ring.write(np.zeros((2, 2, 3), dtype=np.uint8), 30)
        ring.read_latest(timeout=1.0)
        ring.reset_sequence()
        assert ring.read_latest(timeout=0.05) is None
    finally:
        ring.close()
        ring.unlink()


def _spawn_write(shm_name: str, value: int) -> None:
    ring = FrameShmRing.attach(shm_name)
    frame = np.full((2, 2, 3), value, dtype=np.uint8)
    ring.write(frame, 25)
    ring.close()


def test_shm_ComContextoSpawn_PreservaFrame() -> None:
    owner = FrameShmRing.create(max_payload=64)
    try:
        ctx = mp.get_context("spawn")
        proc = ctx.Process(target=_spawn_write, args=(owner.name, 9))
        proc.start()
        proc.join(timeout=15)
        assert proc.exitcode == 0

        item = owner.read_latest(timeout=1.0)
        assert item is not None
        np.testing.assert_array_equal(item.frame, np.full((2, 2, 3), 9, dtype=np.uint8))
        assert item.stream_fps == 25
    finally:
        owner.close()
        owner.unlink()


def test_default_max_payload_Cabe1080p() -> None:
    assert DEFAULT_MAX_PAYLOAD >= 1920 * 1080 * 3
