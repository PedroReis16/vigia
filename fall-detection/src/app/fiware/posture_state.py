from __future__ import annotations

import json
import os
from pathlib import Path

from app.logging import get_logger

logger = get_logger("fiware")


def _posture_state_file() -> Path | None:
    raw_path = (os.getenv("POSTURE_STATUS_FILE") or "").strip()
    if not raw_path:
        return None
    return Path(raw_path)


def read_posture_state() -> tuple[str, str | None]:
    state_file = _posture_state_file()
    if state_file is None or not state_file.exists():
        return "unknown", None

    try:
        content = state_file.read_text(encoding="utf-8").strip()
        if not content:
            return "unknown", None
        payload = json.loads(content)
        state = str(payload.get("posture_state") or "unknown")
        changed_at_raw = payload.get("posture_changed_at")
        changed_at = str(changed_at_raw) if changed_at_raw else None
        return state, changed_at
    except Exception as exc:  # pragma: no cover
        logger.warning("erro lendo POSTURE_STATUS_FILE: {}", exc)
        return "unknown", None


def write_posture_state(posture_state: str, posture_changed_at: str) -> None:
    state_file = _posture_state_file()
    if state_file is None:
        return

    state_file.parent.mkdir(parents=True, exist_ok=True)
    state_file.write_text(
        json.dumps(
            {
                "posture_state": posture_state,
                "posture_changed_at": posture_changed_at,
            }
        ),
        encoding="utf-8",
    )
