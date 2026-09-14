"""Protocolo do miolo de classificação de queda."""

from __future__ import annotations

from typing import Protocol

from capture.classifiers.types import FallDecision, PoseObservation


class FallClassifier(Protocol):
    """Strategy: pós-YOLO → decisão de queda."""

    def process(self, observations: list[PoseObservation]) -> list[FallDecision]:
        """Consome poses do frame e devolve decisões (pode ser lista vazia)."""
        ...
