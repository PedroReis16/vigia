from enum import Enum


class FallState(Enum):
    """
    Estado do detector de queda
    """
    NORMAL = 0
    SUSPECT = 1
    FALL = 2


class FallDetector:
    """
    Detector de queda
    """
    def __init__(self, score_threshold: float = 0.65, persistence_frames: int = 5):
        """
        Inicializa o detector de queda
        """
        self.score_threshold = score_threshold          # Nível de corte para considerar um evento como suspeito de queda
        self.persistence_frames = persistence_frames    # Número de frames consecutivos para considerar um evento de queda como suspeito
        self._consecutive_frames = 0                    # Contador de frames positivos
        self.state = FallState.NORMAL

    def update(self, score: float) -> FallState:
        """
        Atualiza o estado do detector de queda
        """
        if score > self.score_threshold:
            self._consecutive_frames += 1
        else:
            self._consecutive_frames = 0

        if self._consecutive_frames >= self.persistence_frames:
            self.state = FallState.SUSPECT

        return self.state
