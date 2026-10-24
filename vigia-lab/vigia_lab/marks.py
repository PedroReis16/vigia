"""Marcas do início e do fim da queda feitas pela operadora (Ana) e política de duração.

Puro, sem I/O. Tempos em segundos relativos ao 1º frame gravado.

- `m` marca o INÍCIO da queda (perda de equilíbrio / começo da descida);
- `n` marca o FIM (contato com o chão); só vale depois do início;
- `u` desfaz a última marca (engano de tecla).
As marcas ao vivo têm o atraso de reação da operadora (~0,4 s); o processamento
offline calcula `event_t_auto` (curva do tronco) e guarda a diferença.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal


@dataclass
class EventMarks:
    start_t: float | None = None
    end_t: float | None = None
    _history: list[str] = field(default_factory=list)

    def press_start(self, t: float) -> bool:
        """Define (ou redefine) o início; descarta um fim que ficaria antes dele."""
        self.start_t = t
        if self.end_t is not None and self.end_t <= t:
            self.end_t = None
        self._history.append("start")
        return True

    def press_end(self, t: float) -> bool:
        """O fim só vale depois do início."""
        if self.start_t is None or t <= self.start_t:
            return False
        self.end_t = t
        self._history.append("end")
        return True

    def undo(self) -> bool:
        if not self._history:
            return False
        last = self._history.pop()
        if last == "end":
            self.end_t = None
        else:
            self.start_t = None
            self.end_t = None if "start" not in self._history else self.end_t
        return True

    def as_dict(self) -> dict[str, float | None]:
        return {"event_start_t": self.start_t, "event_end_t": self.end_t}


@dataclass(frozen=True)
class DurationPolicy:
    """'fixed' = duração padronizada (padrão 10 s); 'manual' = a Ana para a gravação."""

    mode: Literal["fixed", "manual"] = "fixed"
    fixed_s: float = 10.0

    def finished(self, elapsed_s: float, stop_requested: bool) -> bool:
        if stop_requested:
            return True
        return self.mode == "fixed" and elapsed_s >= self.fixed_s

    def remaining(self, elapsed_s: float) -> float | None:
        """Tempo restante a exibir; None no modo manual."""
        if self.mode != "fixed":
            return None
        return max(self.fixed_s - elapsed_s, 0.0)

    def toggled(self) -> "DurationPolicy":
        return DurationPolicy("manual" if self.mode == "fixed" else "fixed", self.fixed_s)
