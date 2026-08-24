"""
Ring buffer latest-only de frames BGR via multiprocessing.shared_memory.
"""

from __future__ import annotations

import struct
import time
from typing import NamedTuple

import numpy as np
from multiprocessing.shared_memory import SharedMemory

_HEADER_FMT = "<IIIIIQ"
_HEADER_SIZE = struct.calcsize(_HEADER_FMT)
DEFAULT_MAX_PAYLOAD = 1920 * 1080 * 3


class FrameRead(NamedTuple):
    frame: np.ndarray
    stream_fps: int


class FrameShmRing:
    """
    Um slot em shared memory: o writer sobrescreve; o reader consome só quando
    ``sequence`` muda (latest-only).
    """

    def __init__(self, shm: SharedMemory, *, owns_shm: bool) -> None:
        self._shm = shm
        self._owns_shm = owns_shm
        self._max_payload = max(len(shm.buf) - _HEADER_SIZE, 0)
        self._last_read_seq = 0

    @property
    def name(self) -> str:
        return self._shm.name

    @classmethod
    def create(cls, max_payload: int = DEFAULT_MAX_PAYLOAD) -> FrameShmRing:
        size = _HEADER_SIZE + max_payload
        shm = SharedMemory(create=True, size=size)
        cls._zero_header(shm)
        return cls(shm, owns_shm=True)

    @classmethod
    def attach(cls, shm_name: str) -> FrameShmRing:
        shm = SharedMemory(name=shm_name)
        return cls(shm, owns_shm=False)

    @staticmethod
    def _zero_header(shm: SharedMemory) -> None:
        struct.pack_into(_HEADER_FMT, shm.buf, 0, 0, 0, 0, 0, 0, 0)

    def write(self, frame: np.ndarray, stream_fps: int) -> bool:
        """
        Copia o frame para o bloco e incrementa ``sequence``.
        Retorna False se frame vazio ou maior que o buffer.
        """
        if frame is None or getattr(frame, "size", 0) == 0:
            return False

        contiguous = np.ascontiguousarray(frame)
        height, width = contiguous.shape[:2]
        channels = 1 if contiguous.ndim == 2 else contiguous.shape[2]
        payload = contiguous.tobytes()
        if len(payload) > self._max_payload:
            return False

        buf = self._shm.buf
        _, _, _, _, _, seq = struct.unpack_from(_HEADER_FMT, buf, 0)
        next_seq = seq + 1
        buf[_HEADER_SIZE : _HEADER_SIZE + len(payload)] = payload
        struct.pack_into(
            _HEADER_FMT,
            buf,
            0,
            width,
            height,
            channels,
            stream_fps,
            len(payload),
            next_seq,
        )
        return True

    def read_latest(self, timeout: float = 0.2) -> FrameRead | None:
        """
        Devolve o frame mais recente se ``sequence`` mudou desde a última leitura.
        """
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            width, height, channels, stream_fps, payload_len, seq = struct.unpack_from(
                _HEADER_FMT, self._shm.buf, 0
            )
            if seq == 0 or seq == self._last_read_seq or payload_len <= 0 or payload_len > self._max_payload:
                time.sleep(0.001)
                continue

            raw = bytes(self._shm.buf[_HEADER_SIZE : _HEADER_SIZE + payload_len])
            self._last_read_seq = seq

            if channels == 1:
                frame = np.frombuffer(raw, dtype=np.uint8).reshape((height, width)).copy()
            else:
                frame = (
                    np.frombuffer(raw, dtype=np.uint8)
                    .reshape((height, width, channels))
                    .copy()
                )
            return FrameRead(frame=frame, stream_fps=stream_fps or 30)

        return None

    def reset_sequence(self) -> None:
        """Invalida frames pendentes (ex.: após stream_off)."""
        width, height, channels, stream_fps, payload_len, _ = struct.unpack_from(
            _HEADER_FMT, self._shm.buf, 0
        )
        struct.pack_into(
            _HEADER_FMT,
            self._shm.buf,
            0,
            width,
            height,
            channels,
            stream_fps,
            payload_len,
            0,
        )
        self._last_read_seq = 0

    def close(self) -> None:
        self._shm.close()

    def unlink(self) -> None:
        if self._owns_shm:
            try:
                self._shm.unlink()
            except FileNotFoundError:
                pass
