"""Testes de integração: clientes em integration/requests contra servidor HTTP local."""

from __future__ import annotations

from uuid import uuid4

import pytest
from aiohttp.test_utils import TestServer

from app.integration.models.vigia_settings import VigiaSettings
from app.integration.requests.get_fiware_device_by_id import GetFiwareDeviceById
from app.integration.requests.get_orion_entity_by_id import GetOrionEntityById
from app.integration.requests.post_create_device_heartbeat_entity import (
    PostCreateDeviceHeartbeatEntity,
)
from app.integration.requests.post_device_heartbeat import PostDeviceHeartbeat
from app.integration.requests.post_new_vigia_device import PostNewVigiaDevice
from app.integration.requests.post_update_device_heartbeat_attrs import (
    PostUpdateDeviceHeartbeatAttrs,
)
from app.integration.requests.post_vigia_command import PostVigiaCommand
from app.integration.requests.put_vigia_device import PutVigiaDevice


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_fiware_device_by_id_execute_async_given_live_server_should_return_settings(
    fiware_http_integration: tuple[TestServer, dict],
) -> None:
    _, state = fiware_http_integration
    device_id = uuid4()

    result = await GetFiwareDeviceById().execute_async(device_id)

    assert isinstance(result, VigiaSettings)
    assert result.device_id == device_id
    assert any(c[0] == "GET" and "iot/devices" in c[1] for c in state["calls"])


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_fiware_device_by_id_execute_async_given_not_found_should_return_none(
    fiware_http_integration: tuple[TestServer, dict],
) -> None:
    _, state = fiware_http_integration
    state["get_device_status"] = 404

    result = await GetFiwareDeviceById().execute_async(uuid4())

    assert result is None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_fiware_device_by_id_execute_async_given_html_response_should_return_none(
    fiware_http_integration: tuple[TestServer, dict],
) -> None:
    _, state = fiware_http_integration
    state["get_device_html"] = True

    result = await GetFiwareDeviceById().execute_async(uuid4())

    assert result is None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_post_new_vigia_device_execute_async_given_live_server_should_succeed(
    fiware_http_integration: tuple[TestServer, dict],
) -> None:
    _, state = fiware_http_integration
    settings = VigiaSettings(device_id=uuid4())

    await PostNewVigiaDevice().execute_async(settings)

    assert any(c[0] == "POST" and c[1].endswith("/iot-agent/iot/devices") for c in state["calls"])


@pytest.mark.integration
@pytest.mark.asyncio
async def test_put_vigia_device_execute_async_given_live_server_should_succeed(
    fiware_http_integration: tuple[TestServer, dict],
) -> None:
    _, state = fiware_http_integration
    settings = VigiaSettings(device_id=uuid4())

    await PutVigiaDevice().execute_async(settings)

    assert any(c[0] == "PUT" and "/iot/devices/" in c[1] for c in state["calls"])


@pytest.mark.integration
@pytest.mark.asyncio
async def test_post_vigia_command_execute_async_given_live_server_should_succeed(
    fiware_http_integration: tuple[TestServer, dict],
) -> None:
    _, state = fiware_http_integration
    settings = VigiaSettings(device_id=uuid4())

    await PostVigiaCommand().execute_async(settings)

    assert any(
        c[0] == "POST" and "/orion/v2/registrations" in c[1] for c in state["calls"]
    )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_orion_entity_by_id_execute_async_given_live_server_should_return_json(
    fiware_http_integration: tuple[TestServer, dict],
) -> None:
    _, state = fiware_http_integration
    entity_id = "urn:ngsi-ld:VigiaCam:abcd"
    state["entities"][entity_id] = {"id": entity_id, "type": "VigiaCam"}

    result = await GetOrionEntityById().execute_async(entity_id)

    assert result == {"id": entity_id, "type": "VigiaCam"}


@pytest.mark.integration
@pytest.mark.asyncio
async def test_post_create_device_heartbeat_entity_execute_async_given_live_server_should_succeed(
    fiware_http_integration: tuple[TestServer, dict],
) -> None:
    _, state = fiware_http_integration

    await PostCreateDeviceHeartbeatEntity().execute_async(
        {"id": "urn:test:hb", "type": "VigiaCam"}
    )

    assert any(c[0] == "POST" and c[1].endswith("/orion/v2/entities") for c in state["calls"])


@pytest.mark.integration
@pytest.mark.asyncio
async def test_post_update_device_heartbeat_attrs_execute_async_given_live_server_should_succeed(
    fiware_http_integration: tuple[TestServer, dict],
) -> None:
    _, state = fiware_http_integration

    await PostUpdateDeviceHeartbeatAttrs().execute_async(
        "urn:test:hb",
        {"heartbeatAt": {"type": "DateTime", "value": "2026-04-21T12:00:00Z"}},
    )

    assert any("/attrs" in c[1] for c in state["calls"])


@pytest.mark.integration
@pytest.mark.asyncio
async def test_post_device_heartbeat_execute_async_given_live_server_should_succeed(
    fiware_http_integration: tuple[TestServer, dict],
) -> None:
    _, state = fiware_http_integration

    await PostDeviceHeartbeat().execute_async({"id": "urn:test:legacy"})

    assert any(c[0] == "POST" and "/orion/v2/entities" in c[1] for c in state["calls"])
