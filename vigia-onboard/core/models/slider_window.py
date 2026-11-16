"""Janelas deslizantes por person_id."""

from collections import deque
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class PersonWindow:
    """Janela deslizante destinada a um ID."""

    window: deque = field(default_factory=deque)
    last_seen: float = 0.0


class SlidingWindowManager:
    """Mantém uma janela deslizante por ID e limpa IDs fora de cena."""

    def __init__(self, window_size: int) -> None:
        self.window_size = window_size
        self._windows: dict[int, PersonWindow] = {}

    def update(self, frame_result: dict[int, dict[str, Any]]) -> list[int]:
        """
        Insere os dados do frame nas janelas dos IDs presentes.

        Retorna a lista de IDs cuja janela está cheia.
        """
        ready: list[int] = []

        for person_id, data in frame_result.items():
            pw = self._windows.get(person_id)
            if pw is None:
                pw = PersonWindow(window=deque(maxlen=self.window_size))
                self._windows[person_id] = pw

            pw.window.append(data)
            pw.last_seen = data["timestamp"]

            if len(pw.window) == self.window_size:
                ready.append(person_id)

        return ready

    def get_window(self, person_id: int) -> Optional[deque]:
        pw = self._windows.get(person_id)
        return pw.window if pw else None

    def get_fill_status(self) -> dict[int, tuple[int, int]]:
        return {
            person_id: (len(pw.window), self.window_size)
            for person_id, pw in self._windows.items()
        }

    def cleanup(self, active_person_ids: set[int]) -> None:
        """Remove janelas de IDs que saíram de cena."""
        stale = [pid for pid in self._windows if pid not in active_person_ids]
        for pid in stale:
            del self._windows[pid]
