"""Classificador de queda persistido na chave classifier de device.json."""

from __future__ import annotations

import logging
from typing import Literal

from shared.device_config import read_document, replace_section

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
    data = read_document()
    if "classifier" not in data:
        return DEFAULT_CLASSIFIER
    return _normalize(data.get("classifier"))


def set_classifier(classifier: ClassifierId) -> None:
    """Grava a chave classifier em device.json (chmod 600)."""
    replace_section("classifier", _normalize(classifier))


def ensure_classifier_config() -> ClassifierId:
    """Materializa classifier válido (default math) se ausente ou inválido."""
    data = read_document()
    current = get_classifier()
    stored = data.get("classifier")
    needs_write = "classifier" not in data or stored not in VALID_CLASSIFIERS
    if needs_write:
        set_classifier(current)
        log.info("classifier materializado em device.json: %s", current)
    return current
