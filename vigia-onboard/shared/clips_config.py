"""Preferência local de armazenamento de clipes (clips.json)."""

from __future__ import annotations

import json
import logging
import os
import tempfile

from shared.settings import get_clips_config_path
from shared.stream_control import set_clips_enabled

logger = logging.getLogger(__name__)


def clips_enabled() -> bool:
    """Lê clips.json. Ausente ou inválido vale desligado."""
    path = get_clips_config_path()
    if not path.exists():
        return False
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    if not isinstance(data, dict):
        return False
    return data.get("enabled") is True


def save_clips_enabled(enabled: bool) -> None:
    """Grava clips.json de forma atómica (chmod 600)."""
    path = get_clips_config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps({"enabled": bool(enabled)})
    fd, tmp_name = tempfile.mkstemp(
        dir=path.parent, prefix=".clips-", suffix=".json"
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
    logger.info("clips.json enabled=%s", bool(enabled))


def apply_persisted_clips() -> None:
    """Copia clips.json para o ControlShm sem regravar o ficheiro."""
    enabled = clips_enabled()
    set_clips_enabled(enabled)
    logger.info("clips persistidos aplicados enabled=%s", enabled)
