"""Provisionamento local do dispositivo (identidade, BLE, Wi‑Fi)."""

from .identity import is_provisioned, load_or_create_identity

__all__ = [
    "is_provisioned",
    "load_or_create_identity",
]
