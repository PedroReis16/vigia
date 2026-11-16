"""Protocolo do miolo de classificação de queda."""

from __future__ import annotations

from typing import Protocol

from core.models.types import FallDecision, PoseObservation


class FallClassifier(Protocol):
    """Strategy: pontos filtrados → decisão de queda."""

    def process(self, observations: list[PoseObservation]) -> list[FallDecision]:
        """Consome poses do frame e devolve decisões (pode ser lista vazia)."""
        ...

    def cleanup(self, active_person_ids: set[int]) -> None:
        """Remove estado de IDs fora de cena."""
        ...
