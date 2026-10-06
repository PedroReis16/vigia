"""Settings do control plane: reexporta o `.env` partilhado do onboard."""

from shared.settings import (
    PROD_DATA_DIR,
    PROD_OTA_DIR,
    Settings,
    get_classifier_path,
    get_identity_path,
    get_network_path,
    get_settings,
    resolve_install_root,
    resolve_ota_dir,
)

__all__ = [
    "PROD_DATA_DIR",
    "PROD_OTA_DIR",
    "Settings",
    "get_classifier_path",
    "get_identity_path",
    "get_network_path",
    "get_settings",
    "resolve_install_root",
    "resolve_ota_dir",
]
