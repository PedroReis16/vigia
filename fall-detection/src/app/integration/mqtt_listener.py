from __future__ import annotations

import asyncio
import json
import os

import paho.mqtt.client as mqtt

from app.fiware.models.vigia_settings import VigiaSettings
from app.integration.command_bus import CommandDispatcher
from app.logging import get_logger

logger = get_logger("integration")


async def listen_mqtt_commands(
    device_settings: VigiaSettings, dispatcher: CommandDispatcher
) -> None:
    mqtt_enabled = (os.getenv("FIWARE_MQTT_ENABLED") or "true").strip().lower()
    if mqtt_enabled in ("0", "false", "no", "off"):
        logger.info("escuta MQTT desabilitada por FIWARE_MQTT_ENABLED")
        while True:
            await asyncio.sleep(60)

    mqtt_host = (os.getenv("FIWARE_MQTT_HOST") or "localhost").strip()
    mqtt_port = int(os.getenv("FIWARE_MQTT_PORT", "1883"))
    mqtt_topic = os.getenv("FIWARE_MQTT_TOPIC") or f"/{device_settings.entity_name}/cmd"
    mqtt_username = (os.getenv("FIWARE_MQTT_USERNAME") or "").strip()
    mqtt_password = (os.getenv("FIWARE_MQTT_PASSWORD") or "").strip()

    loop = asyncio.get_running_loop()
    incoming_queue: asyncio.Queue[tuple[str, dict]] = asyncio.Queue()

    while True:
        client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        if mqtt_username:
            client.username_pw_set(mqtt_username, mqtt_password)

        def on_connect(
            _client: mqtt.Client,
            _userdata: object,
            _flags: mqtt.ConnectFlags,
            reason_code: mqtt.ReasonCode,
            _properties: mqtt.Properties | None = None,
        ) -> None:
            if reason_code.is_failure:
                logger.warning("falha ao conectar MQTT: {}", reason_code)
                return
            _client.subscribe(mqtt_topic, qos=1)
            logger.info("ouvindo topico MQTT: {}", mqtt_topic)

        def on_message(
            _client: mqtt.Client,
            _userdata: object,
            msg: mqtt.MQTTMessage,
        ) -> None:
            raw = msg.payload.decode("utf-8", errors="ignore")
            try:
                body = json.loads(raw) if raw else {}
            except json.JSONDecodeError:
                body = {"raw": raw}

            command_name = str(body.get("command") or body.get("name") or "").strip()
            payload = body.get("payload") if isinstance(body.get("payload"), dict) else body
            if not command_name:
                logger.warning("mensagem MQTT sem comando: {}", raw)
                return
            loop.call_soon_threadsafe(incoming_queue.put_nowait, (command_name, payload))

        client.on_connect = on_connect
        client.on_message = on_message

        try:
            client.connect(mqtt_host, mqtt_port, keepalive=60)
            client.loop_start()
            while True:
                command_name, payload = await incoming_queue.get()
                try:
                    await dispatcher.dispatch(command_name, payload)
                except Exception as exc:
                    logger.warning(
                        "erro ao processar comando '{}': {}", command_name, exc
                    )
        except OSError as exc:
            logger.warning(
                "broker MQTT indisponivel em {}:{}: {}. nova tentativa em 10s.",
                mqtt_host,
                mqtt_port,
                exc,
            )
            await asyncio.sleep(10)
        finally:
            try:
                client.loop_stop()
                client.disconnect()
            except Exception:
                pass
