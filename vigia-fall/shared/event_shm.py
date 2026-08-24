"""
Ring buffer multi-slot de eventos pequenos via multiprocessing.shared_memory.
"""

from __future__ import annotations

import struct
import time
from typing import NamedTuple

from multiprocessing.shared_memory import SharedMemory

from shared.event_types import EVENT_FALL_STATE, EVENT_LOG

_HEADER_FMT = "<QQII"
_HEADER_SIZE = struct.calcsize(_HEADER_FMT)
_SLOT_META_FMT = "<QBBIHdH"
_SLOT_META_SIZE = struct.calcsize(_SLOT_META_FMT)
_DEFAULT_SLOT_COUNT = 8
_DEFAULT_PAYLOAD_MAX = 128


class EventRecord(NamedTuple):
    event_type: int
    level: int
    person_id: int
    capture_ts: float
    payload: str


class EventShmRing:
    """
    Fila circular em shared memory: writer descarta o mais antigo quando cheia.
    Um reader por ring (FIWARE ou log drain).
    """

    def __init__(
        self,
        shm: SharedMemory,
        *,
        slot_count: int,
        payload_max: int,
        owns_shm: bool,
    ) -> None:
        self._shm = shm
        self._slot_count = slot_count
        self._payload_max = payload_max
        self._slot_stride = _SLOT_META_SIZE + payload_max
        self._owns_shm = owns_shm

    @property
    def name(self) -> str:
        return self._shm.name

    @classmethod
    def create(
        cls,
        slot_count: int = _DEFAULT_SLOT_COUNT,
        payload_max: int = _DEFAULT_PAYLOAD_MAX,
    ) -> EventShmRing:
        size = _HEADER_SIZE + slot_count * (_SLOT_META_SIZE + payload_max)
        shm = SharedMemory(create=True, size=size)
        struct.pack_into(_HEADER_FMT, shm.buf, 0, 0, 0, slot_count, payload_max)
        return cls(shm, slot_count=slot_count, payload_max=payload_max, owns_shm=True)

    @classmethod
    def attach(cls, shm_name: str) -> EventShmRing:
        shm = SharedMemory(name=shm_name)
        _, _, slot_count, payload_max = struct.unpack_from(_HEADER_FMT, shm.buf, 0)
        return cls(
            shm,
            slot_count=max(slot_count, 1),
            payload_max=max(payload_max, 1),
            owns_shm=False,
        )

    def _read_header(self) -> tuple[int, int, int, int]:
        write_seq, read_seq, slot_count, payload_max = struct.unpack_from(
            _HEADER_FMT, self._shm.buf, 0
        )
        return write_seq, read_seq, slot_count, payload_max

    def _write_header(
        self,
        write_seq: int,
        read_seq: int,
        slot_count: int | None = None,
        payload_max: int | None = None,
    ) -> None:
        cur_w, cur_r, cur_slots, cur_payload = self._read_header()
        struct.pack_into(
            _HEADER_FMT,
            self._shm.buf,
            0,
            write_seq,
            read_seq,
            slot_count if slot_count is not None else cur_slots,
            payload_max if payload_max is not None else cur_payload,
        )

    def _slot_offset(self, seq_index: int) -> int:
        return _HEADER_SIZE + (seq_index % self._slot_count) * self._slot_stride

    def write(
        self,
        event_type: int,
        payload: str,
        *,
        capture_ts: float = 0.0,
        person_id: int = 0,
        level: int = 0,
    ) -> bool:
        """Enfileira evento. Descarta o mais antigo se a fila estiver cheia."""
        text = (payload or "").encode("utf-8", errors="replace")[: self._payload_max]
        if not text and event_type != EVENT_FALL_STATE:
            return False

        write_seq, read_seq, slot_count, _ = self._read_header()
        while write_seq - read_seq >= slot_count:
            read_seq += 1

        next_seq = write_seq + 1
        slot_idx = (next_seq - 1) % slot_count
        offset = self._slot_offset(slot_idx)
        struct.pack_into(
            _SLOT_META_FMT,
            self._shm.buf,
            offset,
            next_seq,
            event_type,
            level,
            0,
            person_id,
            capture_ts,
            len(text),
        )
        if text:
            self._shm.buf[offset + _SLOT_META_SIZE : offset + _SLOT_META_SIZE + len(text)] = text
        self._write_header(next_seq, read_seq)
        return True

    def read_next(self, timeout: float = 0.05) -> EventRecord | None:
        """Consome o próximo evento ou None se timeout."""
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            write_seq, read_seq, _, _ = self._read_header()
            if read_seq >= write_seq:
                time.sleep(0.001)
                continue

            next_seq = read_seq + 1
            slot_idx = (next_seq - 1) % self._slot_count
            offset = self._slot_offset(slot_idx)
            slot_seq, event_type, level, _, person_id, capture_ts, payload_len = struct.unpack_from(
                _SLOT_META_FMT, self._shm.buf, offset
            )

            if slot_seq != next_seq:
                self._write_header(write_seq, next_seq)
                continue

            payload_len = min(payload_len, self._payload_max)
            raw = bytes(
                self._shm.buf[offset + _SLOT_META_SIZE : offset + _SLOT_META_SIZE + payload_len]
            )
            self._write_header(write_seq, next_seq)
            return EventRecord(
                event_type=event_type,
                level=level,
                person_id=person_id,
                capture_ts=capture_ts,
                payload=raw.decode("utf-8", errors="replace"),
            )

        return None

    def reset(self) -> None:
        """Invalida eventos pendentes."""
        write_seq, _, slot_count, payload_max = self._read_header()
        self._write_header(write_seq, write_seq, slot_count, payload_max)

    def close(self) -> None:
        self._shm.close()

    def unlink(self) -> None:
        if self._owns_shm:
            try:
                self._shm.unlink()
            except FileNotFoundError:
                pass


__all__ = [
    "EVENT_FALL_STATE",
    "EVENT_LOG",
    "EventRecord",
    "EventShmRing",
]
