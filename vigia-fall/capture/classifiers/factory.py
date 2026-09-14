"""Factory do miolo de classificação."""

from __future__ import annotations

from capture.classifiers.base import FallClassifier
from capture.classifiers.config import ClassifierId, get_classifier_id
from capture.classifiers.gru_classifier import GruFallClassifier
from capture.classifiers.math_classifier import MathFallClassifier
from shared import get_settings


def create_classifier(classifier_id: ClassifierId | None = None) -> FallClassifier:
    """Instancia o classificador conforme classifier.json (default math)."""
    cid = classifier_id if classifier_id is not None else get_classifier_id()
    if cid == "gru":
        return GruFallClassifier()
    settings = get_settings()
    return MathFallClassifier(window_size=settings.slider_window_size)
