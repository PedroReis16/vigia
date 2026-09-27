"""Factory do miolo de classificação."""

from __future__ import annotations

from core.classifiers.base import FallClassifier
from core.classifiers.gru_classifier import GruFallClassifier
from core.classifiers.math_classifier import MathFallClassifier
from shared.settings import get_settings


def create_classifier(classifier_id: str | None = None) -> FallClassifier:
    """Instancia o classificador conforme CLASSIFIER (default math). Sem hot-swap."""
    settings = get_settings()
    cid = (classifier_id if classifier_id is not None else settings.classifier).lower()
    if cid == "gru":
        return GruFallClassifier()
    return MathFallClassifier(window_size=settings.slider_window_size)
