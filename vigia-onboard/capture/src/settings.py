from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from .paths import onboard_root


def _parse_capture_source(raw: str) -> int | str:
    """Índice de câmera (ex.: "0") ou caminho/URL de vídeo."""
    value = raw.strip()
    if value.lstrip("-").isdigit():
        return int(value)
    return str(Path(value).expanduser().resolve())


def _parse_bool(raw: str) -> bool:
    return raw.strip().lower() in ("1", "true", "t", "yes", "y")


def _load_onboard_env() -> None:
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    load_dotenv(onboard_root() / ".env")


@dataclass(frozen=True)
class Settings:
    """Configurações de captura."""

    capture_source: int | str = 0
    show_video: bool = False
    show_yolo_plot: bool = False
    capture_loop: bool = False
    yolo_model: str = "yolo26s-pose"

    @classmethod
    def from_env(cls) -> Settings:
        """Carrega as configurações do `.env` da raiz do onboard."""
        _load_onboard_env()
        return cls(
            capture_source=_parse_capture_source(os.getenv("CAPTURE_SOURCE", "0")),
            show_video=_parse_bool(os.getenv("SHOW_VIDEO", "false")),
            show_yolo_plot=_parse_bool(os.getenv("SHOW_YOLO_PLOT", "false")),
            capture_loop=_parse_bool(os.getenv("CAPTURE_LOOP", "false")),
            yolo_model=os.getenv("YOLO_MODEL", "yolo26s-pose"),
        )


@lru_cache
def get_settings() -> Settings:
    """Carrega as configurações de ambiente (singleton)."""
    return Settings.from_env()
