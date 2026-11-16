"""
Ring multi-slot de frames BGR (janela deslizante de clipes) via shared memory.
"""

from __future__ import annotations

import struct
import time
from typing import NamedTuple

import numpy as np
from multiprocessing.shared_memory import SharedMemory

from shared.settings import get_settings

_HEADER_FMT = "<QII"
_HEADER_SIZE = struct.calcsize(_HEADER_FMT)
_SLOT_META_FMT = "<QdIIII"
_SLOT_META_SIZE = struct.calcsize(_SLOT_META_FMT)
DEFAULT_MAX_PAYLOAD = 2 * 1024 * 1024
_JPEG_CHANNELS = 0


class ClipFrame(NamedTuple):
    frame: np.ndarray
    capture_ts: float
    sequence: int


class ClipFrameRing:
    """
    Fila circular de frames: writer descarta o mais antigo quando cheia.
    Usada pelo Process de clips; export futuro faz ``snapshot``.
    """

    def __init__(
        self,
        shm: SharedMemory,
        *,
        slot_count: int,
        max_payload: int,
        owns_shm: bool,
    ) -> None:
        self._shm = shm
        self._slot_count = slot_count
        self._max_payload = max_payload
        self._slot_stride = _SLOT_META_SIZE + max_payload
        self._owns_shm = owns_shm

    @property
    def name(self) -> str:
        return self._shm.name

    @property
    def slot_count(self) -> int:
        return self._slot_count

    @property
    def max_payload(self) -> int:
        return self._max_payload

    @classmethod
    def create(
        cls,
        slot_count: int,
        max_payload: int = DEFAULT_MAX_PAYLOAD,
        name: str | None = None,
    ) -> ClipFrameRing:
        if slot_count < 1:
            raise ValueError("slot_count must be >= 1")
        if max_payload < 1:
            raise ValueError("max_payload must be >= 1")
        size = _HEADER_SIZE + slot_count * (_SLOT_META_SIZE + max_payload)
        shm = SharedMemory(name=name, create=True, size=size)
        struct.pack_into(_HEADER_FMT, shm.buf, 0, 0, slot_count, max_payload)
        return cls(
            shm, slot_count=slot_count, max_payload=max_payload, owns_shm=True
        )

    @classmethod
    def attach(cls, shm_name: str) -> ClipFrameRing:
        shm = SharedMemory(name=shm_name)
        write_seq, slot_count, max_payload = struct.unpack_from(
            _HEADER_FMT, shm.buf, 0
        )
        _ = write_seq
        return cls(
            shm,
            slot_count=max(slot_count, 1),
            max_payload=max(max_payload, 1),
            owns_shm=False,
        )

    @classmethod
    def open_or_create(
        cls,
        shm_name: str | None = None,
        *,
        slot_count: int | None = None,
        max_payload: int | None = None,
    ) -> ClipFrameRing:
        settings = get_settings()
        name = (shm_name or settings.clip_shm_name).strip() or settings.clip_shm_name
        slots = slot_count if slot_count is not None else settings.clip_slot_count
        payload = (
            max_payload if max_payload is not None else settings.clip_max_payload
        )
        try:
            ring = cls.attach(name)
        except FileNotFoundError:
            ring = None
        if ring is not None:
            if ring.slot_count == slots and ring.max_payload == payload:
                return ring
            ring.close()
            _discard_shm(name)
        try:
            return cls.create(slot_count=slots, max_payload=payload, name=name)
        except FileExistsError:
            return cls.attach(name)

    def _slot_offset(self, seq_index: int) -> int:
        return _HEADER_SIZE + (seq_index % self._slot_count) * self._slot_stride

    def push(
        self,
        frame: np.ndarray,
        capture_ts: float | None = None,
        *,
        copy: bool = True,
    ) -> bool:
        """Empilha frame; descarta o mais antigo se o ring estiver cheio."""
        if frame is None or getattr(frame, "size", 0) == 0:
            return False

        height, width = int(frame.shape[0]), int(frame.shape[1])
        channels = 1 if frame.ndim == 2 else int(frame.shape[2])
        if height * width * channels > self._max_payload:
            return False

        stored = np.ascontiguousarray(frame.copy() if copy else frame)
        payload = stored.tobytes()
        if len(payload) > self._max_payload:
            return False
        return self._commit(payload, width, height, channels, capture_ts)

    def push_jpeg(
        self,
        payload: bytes,
        width: int,
        height: int,
        capture_ts: float | None = None,
    ) -> bool:
        """Empilha um JPEG na resolução original (``channels == 0``)."""
        if not payload or width < 1 or height < 1 or len(payload) > self._max_payload:
            return False
        return self._commit(payload, width, height, _JPEG_CHANNELS, capture_ts)

    def _commit(
        self,
        payload: bytes,
        width: int,
        height: int,
        channels: int,
        capture_ts: float | None,
    ) -> bool:
        write_seq, slot_count, max_payload = struct.unpack_from(
            _HEADER_FMT, self._shm.buf, 0
        )
        _ = slot_count, max_payload
        next_seq = write_seq + 1
        offset = self._slot_offset(next_seq - 1)
        ts = time.monotonic() if capture_ts is None else float(capture_ts)
        struct.pack_into(
            _SLOT_META_FMT,
            self._shm.buf,
            offset,
            next_seq,
            ts,
            width,
            height,
            channels,
            len(payload),
        )
        self._shm.buf[
            offset + _SLOT_META_SIZE : offset + _SLOT_META_SIZE + len(payload)
        ] = payload
        struct.pack_into(
            _HEADER_FMT,
            self._shm.buf,
            0,
            next_seq,
            self._slot_count,
            self._max_payload,
        )
        return True

    def __len__(self) -> int:
        write_seq, _, _ = struct.unpack_from(_HEADER_FMT, self._shm.buf, 0)
        return min(int(write_seq), self._slot_count)

    def snapshot(self) -> list[ClipFrame]:
        """Cópia ordenada (mais antigo → mais recente) da janela actual."""
        write_seq, _, _ = struct.unpack_from(_HEADER_FMT, self._shm.buf, 0)
        count = min(int(write_seq), self._slot_count)
        if count == 0:
            return []

        start_seq = int(write_seq) - count + 1
        frames: list[ClipFrame] = []
        for seq in range(start_seq, int(write_seq) + 1):
            offset = self._slot_offset(seq - 1)
            slot_seq, capture_ts, width, height, channels, payload_len = (
                struct.unpack_from(_SLOT_META_FMT, self._shm.buf, offset)
            )
            if slot_seq != seq or payload_len <= 0 or payload_len > self._max_payload:
                continue
            raw = bytes(
                self._shm.buf[
                    offset + _SLOT_META_SIZE : offset + _SLOT_META_SIZE + payload_len
                ]
            )
            if channels == _JPEG_CHANNELS:
                import cv2

                decoded = cv2.imdecode(np.frombuffer(raw, dtype=np.uint8), cv2.IMREAD_COLOR)
                if decoded is None:
                    continue
                frame = np.ascontiguousarray(decoded)
            elif channels == 1:
                frame = np.frombuffer(raw, dtype=np.uint8).reshape((height, width)).copy()
            else:
                frame = (
                    np.frombuffer(raw, dtype=np.uint8)
                    .reshape((height, width, channels))
                    .copy()
                )
            frames.append(
                ClipFrame(frame=frame, capture_ts=capture_ts, sequence=slot_seq)
            )
        return frames

    def reset(self) -> None:
        """Zera a sequência (invalida a janela)."""
        struct.pack_into(
            _HEADER_FMT,
            self._shm.buf,
            0,
            0,
            self._slot_count,
            self._max_payload,
        )

    def close(self) -> None:
        self._shm.close()

    def unlink(self) -> None:
        if self._owns_shm:
            try:
                self._shm.unlink()
            except FileNotFoundError:
                pass


def _discard_shm(name: str) -> None:
    """Remove um ring antigo para recriar com outro número de slots."""
    try:
        shm = SharedMemory(name=name)
    except FileNotFoundError:
        return
    try:
        shm.unlink()
    except FileNotFoundError:
        pass
    finally:
        shm.close()


__all__ = [
    "DEFAULT_MAX_PAYLOAD",
    "ClipFrame",
    "ClipFrameRing",
]
