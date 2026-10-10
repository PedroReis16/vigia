"""Preferência local de blur nas capturas (blur.json)."""

from __future__ import annotations

import json
import logging
import os
import tempfile

from shared.settings import get_blur_config_path, get_settings
from shared.stream_control import set_blur_enabled

logger = logging.getLogger(__name__)


def blur_enabled() -> bool:
    """Lê blur.json. Ausente usa BLUR_VIDEO. Inválido vale desligado."""
    path = get_blur_config_path()
    if not path.exists():
        return bool(get_settings().blur_video)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    if not isinstance(data, dict):
        return False
    return data.get("enabled") is True


def save_blur_enabled(enabled: bool) -> None:
    """Grava blur.json de forma atómica (chmod 600)."""
    path = get_blur_config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps({"enabled": bool(enabled)})
    fd, tmp_name = tempfile.mkstemp(
        dir=path.parent, prefix=".blur-", suffix=".json"
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(payload)
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
    logger.info("blur.json enabled=%s", bool(enabled))


def apply_persisted_blur() -> None:
    """Copia blur.json (ou BLUR_VIDEO) para o ControlShm sem regravar o ficheiro."""
    enabled = blur_enabled()
    set_blur_enabled(enabled)
    logger.info("blur persistido aplicado enabled=%s", enabled)
