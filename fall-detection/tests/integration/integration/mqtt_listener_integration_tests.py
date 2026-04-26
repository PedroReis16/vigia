"""Integração: mqtt_listener com broker simulado (FakeMQTTClient)."""

from __future__ import annotations

import asyncio
from unittest.mock import patch
from uuid import uuid4

import pytest

from app.fiware.models.vigia_settings import VigiaSettings
from app.integration.command_bus import (
    _CUSTOM_HANDLERS,
    build_dispatcher,
    register_command_handler,
)
from app.integration.mqtt_listener import listen_mqtt_commands
from app.integration.types import IntegrationContext

from .integration_settings_helpers import minimal_integration_settings
from .mqtt_fake_client import (
    FakeMQTTClient,
    fiware_command_payload,
    fiware_name_payload,
)


@pytest.fixture(autouse=True)
def clear_custom_command_handlers() -> None:
    _CUSTOM_HANDLERS.clear()
    yield
    _CUSTOM_HANDLERS.clear()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_listen_mqtt_given_command_field_should_dispatch_handler(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("FIWARE_MQTT_ENABLED", "true")
    monkeypatch.setenv("FIWARE_MQTT_TOPIC", "/integration/cmd")

    received: list[dict] = []

    async def probe(payload: dict) -> None:
        received.append(payload)

    register_command_handler("mqtt_probe", probe)

    FakeMQTTClient.reset([fiware_command_payload("mqtt_probe", {"detail": "ok"})])

    ctx = IntegrationContext(
        settings=minimal_integration_settings(),
        device_settings=VigiaSettings(device_id=uuid4()),
    )
    dispatcher = build_dispatcher(ctx)

    with patch(
        "app.integration.mqtt_listener.mqtt.Client",
        FakeMQTTClient,
    ):
        task = asyncio.create_task(
            listen_mqtt_commands(ctx.device_settings, dispatcher)
        )
        async def wait_dispatch() -> None:
            while not received:
                await asyncio.sleep(0.01)

        try:
            await asyncio.wait_for(wait_dispatch(), timeout=2.0)
        finally:
            task.cancel()
            with pytest.raises(asyncio.CancelledError):
                await task

    assert received and received[0].get("command") == "mqtt_probe"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_listen_mqtt_given_name_field_should_dispatch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("FIWARE_MQTT_ENABLED", "true")
    monkeypatch.setenv("FIWARE_MQTT_TOPIC", "/integration/cmd")

    received: list[dict] = []

    async def probe(payload: dict) -> None:
        received.append(payload)

    register_command_handler("from_name", probe)

    FakeMQTTClient.reset([fiware_name_payload("from_name")])

    ctx = IntegrationContext(
        settings=minimal_integration_settings(),
        device_settings=VigiaSettings(device_id=uuid4()),
    )
    dispatcher = build_dispatcher(ctx)

    with patch("app.integration.mqtt_listener.mqtt.Client", FakeMQTTClient):
        task = asyncio.create_task(
            listen_mqtt_commands(ctx.device_settings, dispatcher)
        )
        async def wait_dispatch() -> None:
            while not received:
                await asyncio.sleep(0.01)

        try:
            await asyncio.wait_for(wait_dispatch(), timeout=2.0)
        finally:
            task.cancel()
            with pytest.raises(asyncio.CancelledError):
                await task

    assert received


@pytest.mark.integration
@pytest.mark.asyncio
async def test_listen_mqtt_given_invalid_json_should_log_without_dispatch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("FIWARE_MQTT_ENABLED", "true")
    monkeypatch.setenv("FIWARE_MQTT_TOPIC", "/integration/cmd")

    logged_warnings: list[str] = []

    def fake_warning(message: str, *_args: object) -> None:
        logged_warnings.append(message)

    monkeypatch.setattr("app.integration.mqtt_listener.logger.warning", fake_warning)

    captured: list[dict] = []

    async def probe(payload: dict) -> None:
        captured.append(payload)

    register_command_handler("never_fired", probe)

    FakeMQTTClient.reset([b"{not-json"])

    ctx = IntegrationContext(
        settings=minimal_integration_settings(),
        device_settings=VigiaSettings(device_id=uuid4()),
    )
    dispatcher = build_dispatcher(ctx)

    with patch("app.integration.mqtt_listener.mqtt.Client", FakeMQTTClient):
        task = asyncio.create_task(
            listen_mqtt_commands(ctx.device_settings, dispatcher)
        )
        await asyncio.sleep(0.08)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task

    assert not captured
    assert any("sem comando" in message.lower() for message in logged_warnings)
