"""
Flags de controlo stream/clips via shared memory nomeada.

Integration escreve; capture e os Processes filhos leem. Processos Make
não partilham ``multiprocessing.Event``.
"""

from __future__ import annotations

import logging
import struct
from multiprocessing.shared_memory import SharedMemory

from shared.settings import get_settings

logger = logging.getLogger(__name__)

_HEADER_FMT = "<BB"
_HEADER_SIZE = struct.calcsize(_HEADER_FMT)

_control: "StreamControlShm | None" = None


class StreamControlShm:
    """Bloco mínimo: ``stream_on`` e ``clips_enabled`` (1 byte cada)."""

    def __init__(self, shm: SharedMemory, *, owns_shm: bool) -> None:
        self._shm = shm
        self._owns_shm = owns_shm

    @property
    def name(self) -> str:
        return self._shm.name

    @classmethod
    def open_or_create(cls, shm_name: str | None = None) -> StreamControlShm:
        name = (shm_name or get_settings().stream_control_shm_name).strip() or (
            get_settings().stream_control_shm_name
        )
        try:
            shm = SharedMemory(name=name)
            return cls(shm, owns_shm=False)
        except FileNotFoundError:
            pass
        try:
            shm = SharedMemory(name=name, create=True, size=_HEADER_SIZE)
            shm.buf[:_HEADER_SIZE] = struct.pack(_HEADER_FMT, 0, 0)
            return cls(shm, owns_shm=True)
        except FileExistsError:
            shm = SharedMemory(name=name)
            return cls(shm, owns_shm=False)

    def _read(self) -> tuple[bool, bool]:
        stream_on, clips_enabled = struct.unpack_from(_HEADER_FMT, self._shm.buf, 0)
        return bool(stream_on), bool(clips_enabled)

    def _write(self, stream_on: bool, clips_enabled: bool) -> None:
        self._shm.buf[:_HEADER_SIZE] = struct.pack(
            _HEADER_FMT, 1 if stream_on else 0, 1 if clips_enabled else 0
        )

    @property
    def stream_on(self) -> bool:
        return self._read()[0]

    @property
    def clips_enabled(self) -> bool:
        return self._read()[1]

    def set_stream_on(self, enabled: bool) -> None:
        _, clips = self._read()
        self._write(bool(enabled), clips)

    def set_clips_enabled(self, enabled: bool) -> None:
        stream_on, _ = self._read()
        self._write(stream_on, bool(enabled))

    def close(self) -> None:
        self._shm.close()

    def unlink(self) -> None:
        if self._owns_shm:
            try:
                self._shm.unlink()
            except FileNotFoundError:
                pass


def _ensure_control() -> StreamControlShm | None:
    global _control
    if _control is not None:
        return _control
    try:
        _control = StreamControlShm.open_or_create()
    except Exception as error:
        logger.warning("Control SHM indisponível: %s", error)
        _control = None
    return _control


def get_stream_on() -> bool:
    """True se FIWARE pediu streaming RTMP ativo."""
    ctrl = _ensure_control()
    return False if ctrl is None else ctrl.stream_on


def get_clips_enabled() -> bool:
    """True se FIWARE pediu janela de clipes ativa."""
    ctrl = _ensure_control()
    return False if ctrl is None else ctrl.clips_enabled


def set_stream_status(enabled: bool) -> None:
    """Atualiza só a flag stream_on (preserva clips_enabled)."""
    ctrl = _ensure_control()
    if ctrl is None:
        logger.info("stream_status=%s (sem ControlShm)", enabled)
        return
    ctrl.set_stream_on(bool(enabled))
    logger.info("stream_status=%s", enabled)


def set_clips_enabled(enabled: bool) -> None:
    """Atualiza só a flag clips_enabled (preserva stream_on)."""
    ctrl = _ensure_control()
    if ctrl is None:
        logger.info("clips_enabled=%s (sem ControlShm)", enabled)
        return
    ctrl.set_clips_enabled(bool(enabled))
    logger.info("clips_enabled=%s", enabled)


def reset_stream_control_for_tests() -> None:
    """Liberta o singleton (apenas testes)."""
    global _control
    if _control is not None:
        _control.close()
        _control.unlink()
        _control = None


__all__ = [
    "StreamControlShm",
    "get_clips_enabled",
    "get_stream_on",
    "reset_stream_control_for_tests",
    "set_clips_enabled",
    "set_stream_status",
]
