from __future__ import annotations

import asyncio

from app.config import Settings
from app.integration.command_bus import build_dispatcher
from app.integration.device_sync import (
    ensure_fiware_device_synced,
    load_or_create_local_device_settings,
)
from app.integration.heartbeat import run_heartbeat_loop
from app.integration.mqtt_listener import listen_mqtt_commands
from app.integration.types import IntegrationContext


async def run_integration(settings: Settings) -> None:
    """Inicia integração FIWARE: sync de device + heartbeat + escuta MQTT."""
    device_settings = load_or_create_local_device_settings()
    while True:
        try:
            await ensure_fiware_device_synced(device_settings)
            break
        except Exception as exc:
            print(
                "[integration] falha ao sincronizar device com FIWARE; "
                f"nova tentativa em 10s. detalhe: {exc}"
            )
            await asyncio.sleep(10)
    dispatcher = build_dispatcher(
        IntegrationContext(settings=settings, device_settings=device_settings)
    )
    await asyncio.gather(
        run_heartbeat_loop(settings, device_settings),
        listen_mqtt_commands(device_settings, dispatcher),
    )