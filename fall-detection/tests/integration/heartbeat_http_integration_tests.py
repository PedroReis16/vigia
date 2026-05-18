"""Integração: heartbeat contra Orion simulado (schemas e loop)."""

from __future__ import annotations

import asyncio
from uuid import uuid4

import pytest
from aiohttp.test_utils import TestServer

from app.integration.heartbeat import (
    _sync_heartbeat_schema,
    run_heartbeat_loop,
)
from app.fiware.models.vigia_settings import VigiaSettings
from app.fiware.requests.post_create_device_heartbeat_entity import (
    PostCreateDeviceHeartbeatEntity,
)
from app.fiware.requests.post_update_device_heartbeat_attrs import (
    PostUpdateDeviceHeartbeatAttrs,
)

from .integration_settings_helpers import minimal_integration_settings


@pytest.mark.integration
@pytest.mark.asyncio
async def test_sync_heartbeat_schema_given_entity_missing_should_post_create(
    fiware_http_integration: tuple[TestServer, dict],
) -> None:
    _, state = fiware_http_integration
    state["get_entity_status"] = 404
    settings = VigiaSettings(device_id=uuid4())

    await _sync_heartbeat_schema(
        settings,
        PostCreateDeviceHeartbeatEntity(),
        PostUpdateDeviceHeartbeatAttrs(),
    )

    assert any(c[0] == "POST" and c[1].endswith("/orion/v2/entities") for c in state["calls"])
    assert not any("/attrs" in c[1] for c in state["calls"])


@pytest.mark.integration
@pytest.mark.asyncio
async def test_sync_heartbeat_schema_given_outdated_attribute_types_should_post_attrs(
    fiware_http_integration: tuple[TestServer, dict],
) -> None:
    _, state = fiware_http_integration
    settings = VigiaSettings(device_id=uuid4())
    state["get_entity_body"] = {
        "id": settings.entity_name,
        "type": settings.entity_type,
        "heartbeatAt": {"type": "Text", "value": "x"},
        "deviceIp": {"type": "Text", "value": "10.0.0.1"},
        "captureStatus": {"type": "Text", "value": "running"},
        "coreStatus": {"type": "Text", "value": "running"},
    }

    await _sync_heartbeat_schema(
        settings,
        PostCreateDeviceHeartbeatEntity(),
        PostUpdateDeviceHeartbeatAttrs(),
    )

    assert any("/attrs" in c[1] for c in state["calls"])


@pytest.mark.integration
@pytest.mark.asyncio
async def test_sync_heartbeat_schema_given_entity_matches_schema_should_only_get(
    fiware_http_integration: tuple[TestServer, dict],
) -> None:
    _, state = fiware_http_integration
    settings = VigiaSettings(device_id=uuid4())
    state["get_entity_body"] = {
        "id": settings.entity_name,
        "type": settings.entity_type,
        "heartbeatAt": {"type": "DateTime", "value": "2026-01-01T00:00:00Z"},
        "deviceIp": {"type": "Text", "value": "10.0.0.1"},
        "captureStatus": {"type": "Text", "value": "running"},
        "coreStatus": {"type": "Text", "value": "running"},
        "postureState": {"type": "Text", "value": "unknown"},
        "postureChangedAt": {"type": "DateTime", "value": "2026-01-01T00:00:00Z"},
    }

    await _sync_heartbeat_schema(
        settings,
        PostCreateDeviceHeartbeatEntity(),
        PostUpdateDeviceHeartbeatAttrs(),
    )

    assert any(
        c[0] == "GET" and settings.entity_name in c[1] for c in state["calls"]
    )
    assert not any(c[1].endswith("/attrs") for c in state["calls"])
    assert not any(c[1].endswith("/orion/v2/entities") and c[0] == "POST" for c in state["calls"])


@pytest.mark.integration
@pytest.mark.asyncio
async def test_run_heartbeat_loop_given_synced_entity_should_send_periodic_updates_until_timeout(
    fiware_http_integration: tuple[TestServer, dict],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _, state = fiware_http_integration
    settings_model = VigiaSettings(device_id=uuid4())
    state["get_entity_body"] = {
        "id": settings_model.entity_name,
        "type": settings_model.entity_type,
        "heartbeatAt": {"type": "DateTime", "value": "2026-01-01T00:00:00Z"},
        "deviceIp": {"type": "Text", "value": "10.0.0.1"},
        "captureStatus": {"type": "Text", "value": "running"},
        "coreStatus": {"type": "Text", "value": "running"},
    }

    monkeypatch.setenv("HEARTBEAT_INTERVAL_SECONDS", "60")

    async def immediate_sleep(_seconds: float) -> None:
        return None

    monkeypatch.setattr(
        "app.integration.heartbeat.asyncio.sleep",
        immediate_sleep,
    )

    settings = minimal_integration_settings(integration_interval_seconds=60)

    with pytest.raises(asyncio.TimeoutError):
        await asyncio.wait_for(
            run_heartbeat_loop(settings, settings_model),
            timeout=0.06,
        )

    assert any("/attrs" in c[1] for c in state["calls"])
