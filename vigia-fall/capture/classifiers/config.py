"""Leitura de classifier.json (mesmo contrato do bootstrap)."""

from __future__ import annotations

import json
from typing import Literal

from shared.settings import get_classifier_path

ClassifierId = Literal["math", "gru"]

DEFAULT_CLASSIFIER: ClassifierId = "math"
VALID_CLASSIFIERS: frozenset[str] = frozenset({"math", "gru"})


def _normalize(value: object) -> ClassifierId:
    if isinstance(value, str) and value in VALID_CLASSIFIERS:
        return value  # type: ignore[return-value]
    return DEFAULT_CLASSIFIER


def get_classifier_id() -> ClassifierId:
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
