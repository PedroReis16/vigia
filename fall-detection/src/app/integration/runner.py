from __future__ import annotations

import asyncio

from app.config import Settings
from app.integration.device_registration import bootstrap_device_registration
from app.integration.command_bus import build_dispatcher
from app.integration.heartbeat import run_heartbeat_loop
from app.integration.mqtt_listener import listen_mqtt_commands
from app.integration.types import IntegrationContext


async def run_integration(settings: Settings) -> None:
    """Inicia integração FIWARE: sync de device + heartbeat + escuta MQTT."""
    device_settings = await bootstrap_device_registration()
    dispatcher = build_dispatcher(
        IntegrationContext(settings=settings, device_settings=device_settings)
    )
    await asyncio.gather(
        run_heartbeat_loop(settings, device_settings),
        listen_mqtt_commands(device_settings, dispatcher),
    )