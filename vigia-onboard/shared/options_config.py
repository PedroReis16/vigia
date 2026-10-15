"""Preferências locais de clipes e blur (secção options de device.json)."""

from __future__ import annotations

import logging

from shared.device_config import read_section, update_document
from shared.settings import get_settings
from shared.stream_control import set_blur_enabled, set_clips_enabled

logger = logging.getLogger(__name__)

_KEYS = ("clips", "blur")


def clips_enabled() -> bool:
    """Lê options. Chave ausente, secção ausente ou inválida vale desligado."""
    return _flag("clips", default=False)


def blur_enabled() -> bool:
    """Lê options. Chave ausente usa BLUR_VIDEO. Valor inválido vale desligado."""
    return _flag("blur", default=bool(get_settings().blur_video))


def save_clips_enabled(enabled: bool) -> None:
    """Grava a chave clips em device.json, preservando as outras secções."""
    _save("clips", enabled)


def save_blur_enabled(enabled: bool) -> None:
    """Grava a chave blur em device.json, preservando as outras secções."""
    _save("blur", enabled)


def apply_persisted_clips() -> None:
    """Copia a chave clips para o ControlShm sem regravar o ficheiro."""
    enabled = clips_enabled()
    set_clips_enabled(enabled)
    logger.info("clips persistidos aplicados enabled=%s", enabled)


def apply_persisted_blur() -> None:
    """Copia a chave blur (ou BLUR_VIDEO) para o ControlShm sem regravar o ficheiro."""
    enabled = blur_enabled()
    set_blur_enabled(enabled)
    logger.info("blur persistido aplicado enabled=%s", enabled)


def _flag(key: str, *, default: bool) -> bool:
    stored = _options()
    if key not in stored:
        return default
    return stored[key] is True


def _options() -> dict:
    stored = read_section("options")
    if not isinstance(stored, dict):
        return {}
    return stored


def _save(key: str, enabled: bool) -> None:
    def mutate(document: dict) -> None:
        stored = document.get("options")
        if not isinstance(stored, dict):
            stored = {}
        payload = {
            name: value
            for name in _KEYS
            if (value := stored.get(name)) is True or value is False
        }
        payload[key] = bool(enabled)
        document["options"] = payload

    update_document(mutate)
    logger.info("device.json options.%s=%s", key, bool(enabled))
