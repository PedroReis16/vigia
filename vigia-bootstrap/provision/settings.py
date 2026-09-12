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

# Defaults da placa (systemd). Em debug local use DATA_DIR fora de /opt/vigia.
PROD_DATA_DIR = "/opt/vigia"
PROD_OTA_DIR = "/var/lib/vigia/ota"


def _as_bool(value: str) -> bool:
    return value.strip().lower() in ("1", "true", "t", "yes", "y")


@dataclass(frozen=True)
class Settings:
    data_dir: str = PROD_DATA_DIR
    debug: bool = True
    wifi_mock: bool = False
    wifi_mock_result: str = "success"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings(
        data_dir=os.getenv("DATA_DIR", PROD_DATA_DIR) or PROD_DATA_DIR,
        debug=_as_bool(os.getenv("DEBUG", "true")),
        wifi_mock=_as_bool(os.getenv("WIFI_MOCK", "false")),
        wifi_mock_result=os.getenv("WIFI_MOCK_RESULT", "success").strip().lower(),
    )


def get_identity_path() -> Path:
    return Path(os.path.join(get_settings().data_dir, "identity.json"))


def get_network_path() -> Path:
    return Path(os.path.join(get_settings().data_dir, "network.json"))


def get_classifier_path() -> Path:
    return Path(os.path.join(get_settings().data_dir, "classifier.json"))


def resolve_ota_dir() -> Path:
    """
    Diretório OTA: VIGIA_OTA_DIR explícito, senão {DATA_DIR}/ota em dev local,
    ou /var/lib/vigia/ota na instalação da placa (DATA_DIR=/opt/vigia).
    """
    explicit = (os.getenv("VIGIA_OTA_DIR") or "").strip()
    if explicit:
        return Path(explicit)
    data_dir = (get_settings().data_dir or PROD_DATA_DIR).rstrip("/") or PROD_DATA_DIR
    if data_dir != PROD_DATA_DIR:
        return Path(data_dir) / "ota"
    return Path(PROD_OTA_DIR)


def resolve_install_root() -> Path:
    """Raiz de install do fall: VIGIA_INSTALL_ROOT ou DATA_DIR."""
    explicit = (os.getenv("VIGIA_INSTALL_ROOT") or "").strip()
    if explicit:
        return Path(explicit)
    return Path(get_settings().data_dir or PROD_DATA_DIR)