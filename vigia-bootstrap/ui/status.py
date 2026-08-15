"""Snapshot de estado para o LCD."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass

from provision.actions import fall_is_active
from provision.identity import is_provisioned
from provision.settings import get_network_path
from provision.state import get_pairing_stage, get_phase

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class DeviceSnapshot:
    phase: str
    pairing_stage: str
    provisioned: bool
    fall_active: bool
    ssid: str | None


def _ssid_from_file() -> str | None:
    path = get_network_path()
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text())
        ssid = data.get("ssid")
        return str(ssid) if ssid else None
    except (OSError, json.JSONDecodeError) as exc:
        log.warning("Falha a ler SSID: %s", exc)
        return None


def read_snapshot() -> DeviceSnapshot:
    # SSID só do ficheiro no ciclo do LCD — nmcli no loop bloqueava o I2C.
    ssid = _ssid_from_file()
    return DeviceSnapshot(
        phase=get_phase(),
        pairing_stage=get_pairing_stage(),
        provisioned=is_provisioned(),
        fall_active=fall_is_active(),
        ssid=ssid,
    )
