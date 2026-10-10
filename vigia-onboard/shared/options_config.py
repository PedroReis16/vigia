"""Preferências locais de clipes e blur (options.json)."""

from __future__ import annotations

import json
import logging
import os
import tempfile
from pathlib import Path

from shared.settings import get_options_path, get_settings
from shared.stream_control import set_blur_enabled, set_clips_enabled

logger = logging.getLogger(__name__)

_KEYS = ("clips", "blur")


def clips_enabled() -> bool:
    """Lê options.json. Chave ausente, ficheiro ausente ou inválido vale desligado."""
    return _flag("clips", default=False)


def blur_enabled() -> bool:
    """Lê options.json. Chave ausente usa BLUR_VIDEO. Inválido vale desligado."""
    return _flag("blur", default=bool(get_settings().blur_video))


def save_clips_enabled(enabled: bool) -> None:
    """Grava a chave clips em options.json, preservando as outras."""
    _save("clips", enabled)


def save_blur_enabled(enabled: bool) -> None:
    """Grava a chave blur em options.json, preservando as outras."""
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
    stored = _effective()
    if key not in stored:
        return default
    return stored[key] is True


def _effective() -> dict:
    """options.json, ou os JSON antigos enquanto o ficheiro único ainda não existe."""
    stored = _read_options()
    if stored is not None:
        return stored
    legacy: dict[str, bool] = {}
    clips = _read_legacy_enabled(get_options_path().parent / "clips.json")
    blur = _read_legacy_enabled(get_options_path().parent / "blur.json")
    if clips is not None:
        legacy["clips"] = clips
    if blur is not None:
        legacy["blur"] = blur
    return legacy


def _read_options() -> dict | None:
    """None se options.json não existe. Dict vazio se o conteúdo é inválido."""
    path = get_options_path()
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    if not isinstance(data, dict):
        return {}
    return data


def _read_legacy_enabled(path: Path) -> bool | None:
    """None se o ficheiro antigo não existe. False se existe e não está ligado."""
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    if not isinstance(data, dict):
        return False
    return data.get("enabled") is True


def _save(key: str, enabled: bool) -> None:
    stored = _effective()
    payload = {
        name: value
        for name in _KEYS
        if (value := stored.get(name)) is True or value is False
    }
    payload[key] = bool(enabled)
    path = get_options_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = json.dumps(payload)
    fd, tmp_name = tempfile.mkstemp(
        dir=path.parent, prefix=".options-", suffix=".json"
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(raw)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(tmp_name, 0o600)
        os.replace(tmp_name, path)
    except Exception:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise
    os.chmod(path, 0o600)
    logger.info("options.json %s=%s", key, bool(enabled))
