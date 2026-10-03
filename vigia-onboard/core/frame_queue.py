"""Fila in-process de lotes de points brutos (capture → thread core)."""

from __future__ import annotations

import queue
import time
from functools import lru_cache

from core.models.types import PoseObservation
from shared import get_settings

_QUEUE_MAXSIZE = 2


class FrameQueue:
    """Fila curta com throttle a FRAME_RATE e backpressure (descarta se cheia)."""

    def __init__(self, frame_rate: int, maxsize: int = _QUEUE_MAXSIZE) -> None:
        self._frame_rate = max(frame_rate, 1)
        self._queue: queue.Queue[list[PoseObservation] | None] = queue.Queue(
            maxsize=maxsize
        )
        self._last_classify = 0.0

    def push(self, observations: list[PoseObservation]) -> bool:
        """
        Enfileira o lote se passou o intervalo de FRAME_RATE.

        Returns:
            True se o lote entrou na fila.
        """
        now = time.monotonic()
        if now - self._last_classify < 1.0 / self._frame_rate:
            return False
        try:
            self._queue.put_nowait(observations)
        except queue.Full:
            return False
        self._last_classify = now
        return True

    def get(self, timeout: float | None = None) -> list[PoseObservation] | None:
        return self._queue.get(timeout=timeout)

    def put_sentinel(self) -> None:
        """Acorda o worker para terminar (None)."""
        try:
            self._queue.put_nowait(None)
        except queue.Full:
            try:
                self._queue.get_nowait()
            except queue.Empty:
                pass
            try:
                self._queue.put_nowait(None)
            except queue.Full:
                pass


@lru_cache
def get_frame_queue() -> FrameQueue:
    return FrameQueue(get_settings().frame_rate)
