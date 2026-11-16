"""Frame atual + buffer rolante para clipes."""

from __future__ import annotations

import threading
from collections import deque

import numpy as np


class FrameBus:
    """Partilha o último frame BGR e uma janela rolante para upload de clipes."""

    def __init__(self, clip_window_s: float = 10.0, default_fps: float = 12.0) -> None:
        self._lock = threading.Lock()
        self._latest: np.ndarray | None = None
        self._width = 0
        self._height = 0
        self._fps = max(1.0, float(default_fps))
        self._clip_window_s = max(0.5, float(clip_window_s))
        self._buffer: deque[np.ndarray] = deque(maxlen=self._buffer_maxlen())

    def _buffer_maxlen(self) -> int:
        return max(1, int(self._clip_window_s * self._fps) + 1)

    @property
    def width(self) -> int:
        with self._lock:
            return self._width

    @property
    def height(self) -> int:
        with self._lock:
            return self._height

    @property
    def fps(self) -> float:
        with self._lock:
            return self._fps

    def configure(self, width: int, height: int, fps: float) -> None:
        with self._lock:
            self._width = int(width)
            self._height = int(height)
            self._fps = max(1.0, float(fps))
            self._buffer = deque(self._buffer, maxlen=self._buffer_maxlen())

    def push(self, frame: np.ndarray) -> None:
        if frame is None or frame.size == 0:
            return
        copy = frame.copy()
        with self._lock:
            self._latest = copy
            self._width = int(copy.shape[1])
            self._height = int(copy.shape[0])
            self._buffer.append(copy)

    def latest(self) -> np.ndarray | None:
        with self._lock:
            if self._latest is None:
                return None
            return self._latest.copy()

    def snapshot_clip(self) -> list[np.ndarray]:
        with self._lock:
            return [frame.copy() for frame in self._buffer]
