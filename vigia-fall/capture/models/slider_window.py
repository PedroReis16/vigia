"""
Customização de gerenciamento de janelas deslizantes conforme o Id reconhecidos
"""

from collections import deque
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class PersonWindow:
    """
    Janela deslizante destinada a um ID (person)
    """
    window: deque = field(default_factory=deque())
    last_seen: float = 0.0


class SlidingWindowManager:
    """
    Matém uma janela deslizante por ID, juntamente com o release de janelas ociosas
    """

    def __init__(self, window_size: int, stale_timeout: float) -> None:
        self.window_size = window_size
        self.stale_timeout = stale_timeout
        self._windows: dict[int, PersonWindow] = {}

    def update(self, frame_result: dict[int, dict[str, Any]]) -> list[int]:
        """
        Insere os dados do frame nas janelas dos IDs presentes.

        Retorna a lista de IDs cuja janela está cheia (prontos p/ extração).
        """
        ready: list[int] = []

        for person_id, data in frame_result.items():
            pw = self._windows.get(person_id)

            if pw is None:
                pw = PersonWindow(window=deque(maxlen=self.window_size))
                self._windows[person_id] = pw

            pw.window.append(data)

            timestamp = data["timestamp"]

            pw.last_seen = timestamp
            latest_ts = max(latest_ts, timestamp)

            if len(pw.window) == self.window_size:
                ready.append(person_id)

        self._cleanup_stale(latest_ts)

        return ready

    def get_window(self, person_id: int) -> Optional[deque]:
        """
        Obtém a janela de um ID
        """
        pw = self._windows.get(person_id)
        return pw.window if pw else None

    def _cleanup_stale(self, now: float) -> None:
        """
        Remove as janelas ociosas
        """
        stale = [
            pid
            for pid, pw in self._windows.items()
            if now - pw.last_seen > self.stale_timeout
        ]
        for pid in stale:
            del self._windows[pid]
