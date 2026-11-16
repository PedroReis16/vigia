"""Testes do LiveFrameShm (latest-only)."""

from __future__ import annotations

import numpy as np

from shared.live_frame_shm import DEFAULT_MAX_PAYLOAD, LiveFrameShm


def test_write_read_PreservaConteudoBGR() -> None:
    ring = LiveFrameShm.create(max_payload=64)
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
    ring = LiveFrameShm.create(max_payload=64)
    try:
        assert ring.write(None, 30) is False  # type: ignore[arg-type]
        assert ring.write(np.array([], dtype=np.uint8), 30) is False
        assert ring.read_latest(timeout=0.05) is None
    finally:
        ring.close()
        ring.unlink()


def test_write_SobrescreveUltimoFrame() -> None:
    ring = LiveFrameShm.create(max_payload=64)
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
    ring = LiveFrameShm.create(max_payload=8)
    try:
        # macOS pode arredondar o tamanho do SHM; usar payload > capacidade real.
        huge = np.zeros((ring._max_payload + 1,), dtype=np.uint8)
        # reshape inválido para write — forçar via frame 2D maior que buffer
        rows = (ring._max_payload // 3) + 1
        huge2 = np.zeros((rows, 1, 3), dtype=np.uint8)
        assert ring.write(huge2, 30) is False
    finally:
        ring.close()
        ring.unlink()


def test_reset_sequence_InvalidaLeitura() -> None:
    ring = LiveFrameShm.create(max_payload=64)
    try:
        ring.write(np.zeros((2, 2, 3), dtype=np.uint8), 30)
        ring.read_latest(timeout=1.0)
        ring.reset_sequence()
        assert ring.read_latest(timeout=0.05) is None
    finally:
        ring.close()
        ring.unlink()


def test_default_max_payload_Cabe1080p() -> None:
    assert DEFAULT_MAX_PAYLOAD >= 1920 * 1080 * 3
