"""Throttle equivalente ao `FrameQueue.push` do vigia-onboard (sem a fila).

O vigia só entrega ao classificador um lote a cada 1/FRAME_RATE s. O relógio é
injetável para o mesmo critério valer no reprocessamento offline (relógio do
vídeo) e nos testes.
"""

from __future__ import annotations

import time
from typing import Callable


class Throttle:
    def __init__(self, frame_rate: int, clock: Callable[[], float] = time.monotonic) -> None:
        self._period = 1.0 / max(frame_rate, 1)
        self._clock = clock
        self._last = float("-inf")  # 1º lote sempre passa (relógio virtual começa em 0)
        self.delivered = 0
        self.dropped = 0

    def accept(self) -> bool:
        now = self._clock()
        if now - self._last < self._period:
            self.dropped += 1
            return False
        self._last = now
        self.delivered += 1
        return True
