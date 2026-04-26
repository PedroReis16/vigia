"""Pacote compartilhado com integrações e modelos do FIWARE."""

from app.fiware.device_sync import (
    ensure_fiware_device_registered,
    load_local_device_settings_required,
    load_or_create_local_device_settings,
)
from app.fiware.posture_notifier import FiwarePostureNotifier
from app.fiware.posture_state import read_posture_state, write_posture_state

__all__ = [
    "ensure_fiware_device_registered",
    "FiwarePostureNotifier",
    "load_local_device_settings_required",
    "load_or_create_local_device_settings",
    "read_posture_state",
    "write_posture_state",
]
