"""
Serialização de frames BGR24 para Queue IPC entre captura e streaming.
"""

from __future__ import annotations

from multiprocessing.queues import Queue as MpQueue
from queue import Empty, Full
from typing import Any

import numpy as np

FramePayload = tuple[int, int, int, bytes]


def put_frame(frame_queue: MpQueue, frame: np.ndarray) -> None:
    """
    Enfileira um frame BGR. Se a fila estiver cheia, descarta o mais antigo.
    Frames vazios ou None são ignorados.
    """
    if frame is None or getattr(frame, "size", 0) == 0:
        return

    contiguous = np.ascontiguousarray(frame)
    height, width = contiguous.shape[:2]
    channels = 1 if contiguous.ndim == 2 else contiguous.shape[2]
    payload: FramePayload = (height, width, channels, contiguous.tobytes())

    try:
        frame_queue.put_nowait(payload)
    except Full:
        try:
            frame_queue.get_nowait()
        except Empty:
            pass
        try:
            frame_queue.put_nowait(payload)
        except Full:
            pass


def get_frame(frame_queue: MpQueue, timeout: float = 0.2) -> np.ndarray | None:
    """
    Consome um frame da Queue. Retorna None se a fila estiver vazia no timeout.
    """
    try:
        item: Any = frame_queue.get(timeout=timeout)
    except Empty:
        return None

    if not isinstance(item, tuple) or len(item) != 4:
        return None

    height, width, channels, raw = item
    if channels == 1:
        return np.frombuffer(raw, dtype=np.uint8).reshape((height, width)).copy()
    return (
        np.frombuffer(raw, dtype=np.uint8)
        .reshape((height, width, channels))
        .copy()
    )


def drain_queue(frame_queue: MpQueue) -> None:
    """Esvazia a Queue IPC (ex.: após stream_off)."""
    while True:
        try:
            frame_queue.get_nowait()
        except Empty:
            break
