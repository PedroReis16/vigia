"""Variáveis de ambiente do bootstrap."""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover — opcional no bundle da placa

    def load_dotenv(*_args, **_kwargs) -> bool:
        return False


load_dotenv()


def _as_bool(value: str) -> bool:
    return value.strip().lower() in ("1", "true", "t", "yes", "y")


@dataclass(frozen=True)
class Settings:
    data_dir: str = "/opt/vigia"
    debug: bool = True
    wifi_mock: bool = False
    wifi_mock_result: str = "success"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings(
        data_dir=os.getenv("DATA_DIR", "/opt/vigia") or "/opt/vigia",
        debug=_as_bool(os.getenv("DEBUG", "true")),
        wifi_mock=_as_bool(os.getenv("WIFI_MOCK", "false")),
        wifi_mock_result=os.getenv("WIFI_MOCK_RESULT", "success").strip().lower(),
    )


def get_identity_path() -> Path:
    return Path(os.path.join(get_settings().data_dir, "identity.json"))


def get_network_path() -> Path:
    return Path(os.path.join(get_settings().data_dir, "network.json"))
