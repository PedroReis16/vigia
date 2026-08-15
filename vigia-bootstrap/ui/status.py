"""Snapshot de estado para o LCD."""

from __future__ import annotations

import json
import logging
import subprocess
from dataclasses import dataclass

from provision.actions import fall_is_active
from provision.identity import is_provisioned
from provision.settings import get_network_path
from provision.state import get_phase

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class DeviceSnapshot:
    phase: str
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


def _ssid_from_nmcli() -> str | None:
    try:
        result = subprocess.run(
            ["nmcli", "-t", "-f", "active,ssid", "dev", "wifi"],
            capture_output=True,
            text=True,
            check=False,
            timeout=2,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    for line in result.stdout.splitlines():
        parts = line.split(":", 1)
        if len(parts) == 2 and parts[0] == "yes" and parts[1].strip():
            return parts[1].strip()
    return None


def read_snapshot() -> DeviceSnapshot:
    ssid = _ssid_from_file() or _ssid_from_nmcli()
    return DeviceSnapshot(
        phase=get_phase(),
        provisioned=is_provisioned(),
        fall_active=fall_is_active(),
        ssid=ssid,
    )
