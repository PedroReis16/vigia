"""Identidade persistida em identity.json (sem SQLite)."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from uuid import UUID, uuid4

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519, x25519
from getmac import get_mac_address

from .settings import get_identity_path, get_network_path

log = logging.getLogger(__name__)


@dataclass
class DeviceIdentity:
    device_id: UUID
    device_name: str
    mac_address: str
    sign_priv: ed25519.Ed25519PrivateKey
    ecdh_priv: x25519.X25519PrivateKey


def _raw_priv(key) -> str:
    return key.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption(),
    ).hex()


def _mac_address() -> str:
    main_mac = get_mac_address()
    if not main_mac:
        raise RuntimeError("Não foi possível obter o endereço MAC do dispositivo")
    return main_mac


def _write_identity(identity: DeviceIdentity) -> None:
    path = get_identity_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "device_id": str(identity.device_id),
                "device_name": identity.device_name,
                "mac_address": identity.mac_address,
                "sign_priv": _raw_priv(identity.sign_priv),
                "ecdh_priv": _raw_priv(identity.ecdh_priv),
            }
        )
    )
    path.chmod(0o600)


def is_provisioned() -> bool:
    return get_identity_path().exists() and get_network_path().exists()


def load_or_create_identity() -> DeviceIdentity:
    path = get_identity_path()
    if path.exists():
        data = json.loads(path.read_text())
        sign_priv = ed25519.Ed25519PrivateKey.from_private_bytes(
            bytes.fromhex(data["sign_priv"])
        )
        ecdh_priv = x25519.X25519PrivateKey.from_private_bytes(
            bytes.fromhex(data["ecdh_priv"])
        )
        mac = data.get("mac_address") or _mac_address()
        identity = DeviceIdentity(
            device_id=UUID(data["device_id"]),
            device_name=data["device_name"],
            mac_address=mac,
            sign_priv=sign_priv,
            ecdh_priv=ecdh_priv,
        )
        if "mac_address" not in data:
            _write_identity(identity)
        return identity

    identity = DeviceIdentity(
        device_id=uuid4(),
        device_name=f"Vigia-{uuid4().hex[:8]}",
        mac_address=_mac_address(),
        sign_priv=ed25519.Ed25519PrivateKey.generate(),
        ecdh_priv=x25519.X25519PrivateKey.generate(),
    )
    _write_identity(identity)
    log.info("Identidade criada: %s (%s)", identity.device_name, identity.device_id)
    return identity
