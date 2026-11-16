"""Identidade persistida na secção identity de device.json (sem SQLite)."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from uuid import UUID, uuid4

from getmac import get_mac_address

from shared.device_config import is_provisioned as _config_is_provisioned
from shared.device_config import read_section, replace_section

log = logging.getLogger(__name__)


@dataclass
class DeviceIdentity:
    device_id: UUID
    device_name: str
    mac_address: str


def _mac_address() -> str:
    main_mac = get_mac_address()
    if not main_mac:
        raise RuntimeError("Não foi possível obter o endereço MAC do dispositivo")
    return main_mac


def _write_identity(identity: DeviceIdentity) -> None:
    replace_section(
        "identity",
        {
            "device_id": str(identity.device_id),
            "device_name": identity.device_name,
            "mac_address": identity.mac_address,
        },
    )


def is_provisioned() -> bool:
    return _config_is_provisioned()


def load_or_create_identity() -> DeviceIdentity:
    data = read_section("identity")
    if isinstance(data, dict) and "device_id" in data and "device_name" in data:
        mac = data.get("mac_address") or _mac_address()
        identity = DeviceIdentity(
            device_id=UUID(data["device_id"]),
            device_name=data["device_name"],
            mac_address=mac,
        )
        if "mac_address" not in data or "sign_priv" in data or "ecdh_priv" in data:
            _write_identity(identity)
        return identity

    identity = DeviceIdentity(
        device_id=uuid4(),
        device_name=f"Vigia-{uuid4().hex[:8]}",
        mac_address=_mac_address(),
    )
    _write_identity(identity)
    log.info("Identidade criada: %s (%s)", identity.device_name, identity.device_id)
    return identity
