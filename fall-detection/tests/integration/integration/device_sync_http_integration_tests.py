"""Integração: device_sync contra servidor FIWARE simulado (sem mocks de classe)."""

from __future__ import annotations

from uuid import uuid4

import pytest
from aiohttp.test_utils import TestServer

from app.integration.device_sync import ensure_fiware_device_synced
from app.integration.models.vigia_settings import VigiaSettings


@pytest.mark.integration
@pytest.mark.asyncio
async def test_ensure_fiware_device_synced_given_missing_remote_device_should_register(
    fiware_http_integration: tuple[TestServer, dict],
) -> None:
    _, state = fiware_http_integration
    state["get_device_status"] = 404
    settings = VigiaSettings(device_id=uuid4())

    await ensure_fiware_device_synced(settings)

    paths = [c[1] for c in state["calls"]]
    assert any("/iot/devices/" in p for p in paths)
    assert any(p.endswith("/iot-agent/iot/devices") or p.rstrip("/").endswith("/iot/devices") for p in paths)
    assert any("/orion/v2/registrations" in p for p in paths)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_ensure_fiware_device_synced_given_different_remote_config_should_update(
    fiware_http_integration: tuple[TestServer, dict],
) -> None:
    _, state = fiware_http_integration
    settings = VigiaSettings(device_id=uuid4(), entity_type="VigiaCam")
    state["get_device_body"] = {
        "device_id": str(settings.device_id),
        "entity_type": "OtherType",
        "protocol": "PDI-IoTA-UltraLight",
        "transport": "MQTT",
        "commands": [{"name": "stream"}],
        "attributes": [
            {"name": "stream", "type": "Boolean", "object_id": "st"},
        ],
    }

    await ensure_fiware_device_synced(settings)

    assert any(c[0] == "PUT" for c in state["calls"])
