"""Classificador de queda persistido em classifier.json."""

from __future__ import annotations

import json
import logging
from typing import Literal

from .settings import get_classifier_path

log = logging.getLogger(__name__)

ClassifierId = Literal["math", "gru"]

DEFAULT_CLASSIFIER: ClassifierId = "math"

VALID_CLASSIFIERS: frozenset[str] = frozenset({"math", "gru"})

_LCD_LABELS: dict[ClassifierId, str] = {
    "math": "Matematico",
    "gru": "GRU",
}


def classifier_label(classifier: ClassifierId) -> str:
    """Rótulo LCD (≤16 cols) para o classificador."""
    return _LCD_LABELS[classifier]


def next_classifier(current: ClassifierId) -> ClassifierId:
    return "gru" if current == "math" else "math"


def _normalize(value: object) -> ClassifierId:
    if isinstance(value, str) and value in VALID_CLASSIFIERS:
        return value  # type: ignore[return-value]
    return DEFAULT_CLASSIFIER


def get_classifier() -> ClassifierId:
    """Lê o classificador persistido; ausente/inválido → math."""
    path = get_classifier_path()
    if not path.exists():
        return DEFAULT_CLASSIFIER
    try:
        data = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return DEFAULT_CLASSIFIER
    if not isinstance(data, dict):
        return DEFAULT_CLASSIFIER
    return _normalize(data.get("classifier"))


def set_classifier(classifier: ClassifierId) -> None:
    """Grava classifier.json com chmod 600."""
    normalized = _normalize(classifier)
    path = get_classifier_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"classifier": normalized}))
    path.chmod(0o600)


def ensure_classifier_config() -> ClassifierId:
    """Materializa classifier.json válido (default math) se ausente ou inválido."""
    path = get_classifier_path()
    current = get_classifier()
    needs_write = not path.exists()
    if not needs_write:
        try:
            data = json.loads(path.read_text())
            if (
                not isinstance(data, dict)
                or data.get("classifier") not in VALID_CLASSIFIERS
            ):
                needs_write = True
        except (OSError, json.JSONDecodeError):
            needs_write = True
    if needs_write:
        set_classifier(current)
        log.info("classifier.json materializado: %s", current)
    return current
