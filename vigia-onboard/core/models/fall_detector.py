"""
Detector de queda com persistência e histerese por pessoa.
"""

from dataclasses import dataclass
from enum import Enum


class FallState(Enum):
    """Estado do detector de queda."""

    NORMAL = 0
    SUSPECT = 1
    FALL = 2
    FALSE_POSITIVE = 3


@dataclass(frozen=True)
class FallDetectorConfig:
    """Configuração do detector de queda."""

    threshold_high: float = 0.65
    threshold_low: float = 0.35
    persistence_frames: int = 5
    suspect_max_frames: int = 30
    cooldown_frames: int = 30


@dataclass
class FallDetectorState:
    """Estado persistente do detector (uma instância por pessoa)."""

    consecutive_high: int = 0
    state: FallState = FallState.NORMAL
    frames_in_current_state: int = 0


class FallDetector:
    """Detector de queda."""

    def __init__(self, config: FallDetectorConfig | None = None):
        self.config = config or FallDetectorConfig()
        self._state = FallDetectorState()

    @property
    def state(self) -> FallState:
        return self._state.state

    def update(self, score: float, timestamp: float) -> FallState:
        """Atualiza o contador de persistência e a máquina de estados."""
        del timestamp
        s = self._state
        s.frames_in_current_state += 1

        if s.state == FallState.NORMAL:
            self._update_persistence_counter(score)

            if s.consecutive_high >= self.config.persistence_frames:
                s.state = FallState.SUSPECT
                s.frames_in_current_state = 0
                s.consecutive_high = 0

        elif s.state == FallState.SUSPECT:
            if score < self.config.threshold_low:
                s.state = FallState.NORMAL
                s.consecutive_high = 0
                s.frames_in_current_state = 0
            else:
                s.consecutive_high += 1
                if s.consecutive_high >= self.config.persistence_frames:
                    s.state = FallState.FALL
                    s.frames_in_current_state = 0
                    s.consecutive_high = 0
                elif s.frames_in_current_state >= self.config.suspect_max_frames:
                    s.state = FallState.FALSE_POSITIVE
                    s.frames_in_current_state = 0
                    s.consecutive_high = 0

        elif s.state in (FallState.FALL, FallState.FALSE_POSITIVE):
            if s.frames_in_current_state >= self.config.cooldown_frames:
                s.state = FallState.NORMAL
                s.consecutive_high = 0
                s.frames_in_current_state = 0

        return s.state

    def _update_persistence_counter(self, score: float) -> None:
        """Histerese: só zera o contador se o score cair abaixo de threshold_low."""
        s = self._state
        if score >= self.config.threshold_high:
            s.consecutive_high += 1
        elif score >= self.config.threshold_low:
            pass
        else:
            s.consecutive_high = 0
