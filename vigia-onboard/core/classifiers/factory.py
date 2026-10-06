"""Factory do miolo de classificação."""

from __future__ import annotations

import json

from core.classifiers.base import FallClassifier
from core.classifiers.gru_classifier import GruFallClassifier
from core.classifiers.math_classifier import MathFallClassifier
from shared.settings import get_classifier_path, get_settings

_VALID = frozenset({"math", "gru"})


def read_classifier_id() -> str:
    """``classifier.json`` se existir; senão o fallback ``CLASSIFIER`` do ambiente."""
    path = get_classifier_path()
    if not path.is_file():
        return get_settings().classifier
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return "math"
    if not isinstance(data, dict):
        return "math"
    cid = str(data.get("classifier") or "").strip().lower()
    if cid in _VALID:
        return cid
    return "math"


def create_classifier(classifier_id: str | None = None) -> FallClassifier:
    """Instancia o classificador. Sem hot-swap dentro da sessão."""
    settings = get_settings()
    cid = (
        classifier_id.lower()
        if classifier_id is not None
        else read_classifier_id()
    )
    if cid == "gru":
        return GruFallClassifier()
    return MathFallClassifier(window_size=settings.slider_window_size)
