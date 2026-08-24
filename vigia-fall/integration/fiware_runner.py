"""
Módulo para controle e inicialização da integração entre o dispositivo e o FIWARE
"""

from __future__ import annotations

import json
import logging
import os
import time
from datetime import datetime, timezone
from pathlib import Path as _Path
from queue import Empty
from typing import Any
from urllib.parse import urlparse

import paho.mqtt.client as mqtt
from multiprocessing.queues import Queue as MpQueue
from multiprocessing.synchronize import Event as EventType
from paho.mqtt.enums import CallbackAPIVersion

from integration.fall_ipc import init_fall_queue
from shared import (
    get_device_identity,
    get_network_settings,
    init_stream_event,
    set_stream_status,
)
from shared.log_config import configure_logging

logger = logging.getLogger(__name__)

OTA_DIR = _Path(os.getenv("VIGIA_OTA_DIR", "/var/lib/vigia/ota"))
PENDING_PATH = OTA_DIR / "pending.json"

fiware_client: mqtt.Client | None = None
fiware_topic: str | None = None


def _write_ota_pending(revision: str) -> None:
    revision = (revision or "").strip()
    if not revision:
        logger.warning("device_update sem revision — ignorado")
        return
    OTA_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "revision": revision,
        "received_at": datetime.now(timezone.utc).isoformat(),
    }
    PENDING_PATH.write_text(json.dumps(payload), encoding="utf-8")
    logger.info("OTA pending escrito: %s", revision)


def _parse_ultralight_command(payload: str) -> tuple[str, str, str] | None:
    parts = payload.split("@", 1)
    if len(parts) != 2:
        return None
    device_id = parts[0]
    command, _, value = parts[1].partition("|")
    return device_id, command.strip(), value.strip()


def _on_connect(
    client: mqtt.Client,
    _: Any,
    __: Any,
    ___: Any,
    ____: Any,
) -> None:
    """Callback para conexão com o broker MQTT."""
    logger.info("Connected to MQTT broker")
    if fiware_topic:
        client.subscribe(fiware_topic)


def _on_message(_: mqtt.Client, __: Any, message: mqtt.MQTTMessage) -> None:
    """Callback para recebimento de mensagens do FIWARE."""
    try:
        raw = message.payload.decode()
        logger.info("Message received: %s", raw)
        parsed = _parse_ultralight_command(raw)
        if parsed is None:
            return

        device_id, command, value = parsed
        if device_id != get_device_identity().device_id:
            return

        match command:
            case "stream_on":
                set_stream_status(True)
            case "stream_off":
                set_stream_status(False)
            case "device_update":
                _write_ota_pending(value)
            case _:
                logger.warning("Unknown command: %s", command)
                return

    except Exception as e:
        logger.error("Error parsing message: %s", e)
        return


def _mqtt_endpoint(api_base_url: str) -> tuple[str, int]:
    parsed = urlparse(api_base_url)
    if not parsed.hostname:
        raise ValueError(f"URL inválida: {api_base_url}")
    host = parsed.hostname
    port = 443 if parsed.scheme == "https" else 81
    return host, port


def _create_mqtt_client() -> mqtt.Client:
    client = mqtt.Client(
        callback_api_version=CallbackAPIVersion.VERSION2,
        client_id="vigia-consumer",
        transport="websockets",
    )
    client.ws_set_options(path="/vigia/fiware/mosquitto")
    client.on_connect = _on_connect
    client.on_message = _on_message
    return client


def _publish_fall_state(client: mqtt.Client, topic: str, state: str) -> None:
    """Publica UltraLight ``fall|{state}`` no tópico de attrs."""
    client.publish(topic, f"fall|{state}")
    logger.info("fall_state=%s", state)


def apply_fall_label(
    client: mqtt.Client,
    topic: str,
    label: str,
    last_state: str | None,
) -> str | None:
    """
    Publica fall_state só se o valor canónico mudou.

    Retorna o novo ``last_state`` (igual ao anterior se não houve publish).
    """
    state = normalize_fall_state(label)
    if state == last_state:
        return last_state
    _publish_fall_state(client, topic, state)
    return state


_FALL_STATE_ALIASES: dict[str, str] = {
    "fall": "fall",
    "falling": "fall",
    "normal": "normal",
    "adl": "normal",
    "ok": "normal",
    "suspect": "suspect",
    "false_positive": "false_positive",
    "falsepositive": "false_positive",
}


def normalize_fall_state(label: str) -> str:
    """Mapeia labels dos classificadores para valores canónicos de fall_state."""
    key = (label or "").strip().lower().replace("-", "_").replace(" ", "_")
    return _FALL_STATE_ALIASES.get(key, key or "normal")


def run_fiware(
    stream_event: EventType | None = None,
    fall_queue: MpQueue | None = None,
) -> None:
    """
    Processo FIWARE: cliente MQTT persistente (cmds + attrs) e poll da fall_queue.
    """
    global fiware_client, fiware_topic

    configure_logging("fiware")

    if stream_event is not None:
        init_stream_event(stream_event)
    if fall_queue is not None:
        init_fall_queue(fall_queue)

    identity = get_device_identity()
    network_settings = get_network_settings()

    device_id = identity.device_id
    broker_host, broker_port = _mqtt_endpoint(network_settings.api_base_url)

    fiware_topic = f"/{network_settings.fiware_api_key}/{device_id}/cmd"
    topic_attrs = f"/{network_settings.fiware_api_key}/{device_id}/attrs"

    fiware_client = _create_mqtt_client()
    fiware_client.connect(host=broker_host, port=broker_port, keepalive=60)
    fiware_client.loop_start()

    last_state: str | None = None
    try:
        if fall_queue is None:
            # Sem fila de telemetria: só mantém o cliente MQTT para cmds.
            while True:
                time.sleep(0.5)
        else:
            while True:
                try:
                    label = fall_queue.get(timeout=0.5)
                except Empty:
                    continue
                last_state = apply_fall_label(
                    fiware_client, topic_attrs, label, last_state
                )
    finally:
        fiware_client.loop_stop()
        fiware_client.disconnect()
