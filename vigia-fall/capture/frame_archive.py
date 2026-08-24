"""Ring buffer in-process de frames capturados (extensão futura: clipes de queda)."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class ArchivedFrame:
    """Frame BGR + timestamp monotónico da captura."""

    frame: np.ndarray
    capture_ts: float


class CaptureFrameArchive:
    """
    Retém os últimos N frames lidos pela câmara/vídeo.
    Futuro: SHM ou disco para montagem de clipes na detecção de queda.
    """

    def __init__(self, max_frames: int = 300) -> None:
        if max_frames < 1:
            raise ValueError("max_frames must be >= 1")
        self._max_frames = max_frames
        self._frames: deque[ArchivedFrame] = deque(maxlen=max_frames)

    @property
    def max_frames(self) -> int:
        return self._max_frames

    def __len__(self) -> int:
        return len(self._frames)

    def push(self, frame: np.ndarray, capture_ts: float) -> None:
        """Empilha frame + timestamp; descarta o mais antigo se cheio."""
        self._frames.append(
            ArchivedFrame(frame=frame.copy(), capture_ts=capture_ts)
        )

    def snapshot(self) -> list[tuple[np.ndarray, float]]:
        """Cópia ordenada (mais antigo → mais recente) para montagem de clip."""
        return [(item.frame.copy(), item.capture_ts) for item in self._frames]
