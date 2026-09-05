"""
Módulo para controle e inicialização da integração entre o dispositivo e o FIWARE
"""

from __future__ import annotations

import json
import logging
import time
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlparse

import paho.mqtt.client as mqtt
from multiprocessing.synchronize import Event as EventType
from paho.mqtt.enums import CallbackAPIVersion

from integration.fall_shm import attach_fall_shm
from shared import (
    get_device_identity,
    get_network_settings,
    init_stream_event,
    set_stream_status,
)
from shared.event_types import EVENT_FALL_STATE
from shared.log_config import configure_logging
from shared.settings import resolve_ota_dir

logger = logging.getLogger(__name__)

OTA_DIR = resolve_ota_dir()
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


_LOCAL_MQTT_WS_PATH = "/vigia/fiware/mosquitto"
_PROD_MQTT_WS_PATH = "/"


def _mqtt_host(parsed) -> str:
    hostname = parsed.hostname or ""
    if parsed.scheme == "http":
        return hostname
    labels = hostname.split(".")
    if len(labels) >= 3:
        labels[0] = "mosquitto"
        return ".".join(labels)
    return f"mosquitto.{hostname}"


def _mqtt_port(parsed) -> int:
    if parsed.port is not None:
        return parsed.port
    return 81 if parsed.scheme == "http" else 443


def _mqtt_ws_path(parsed) -> str:
    return _LOCAL_MQTT_WS_PATH if parsed.scheme == "http" else _PROD_MQTT_WS_PATH


def _mqtt_endpoint(api_base_url: str) -> tuple[str, int, str, bool]:
    parsed = urlparse(api_base_url)
    if not parsed.hostname:
        raise ValueError(f"URL inválida: {api_base_url}")
    host = _mqtt_host(parsed)
    port = _mqtt_port(parsed)
    path = _mqtt_ws_path(parsed)
    use_tls = parsed.scheme == "https"
    logger.info("MQTT endpoint: %s:%s%s", host, port, path)
    return host, port, path, use_tls


def _create_mqtt_client(ws_path: str, use_tls: bool) -> mqtt.Client:
    client = mqtt.Client(
        callback_api_version=CallbackAPIVersion.VERSION2,
        client_id="vigia-consumer",
        transport="websockets",
    )
    client.ws_set_options(path=ws_path)
    if use_tls:
        client.tls_set()
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
    fall_shm_name: str | None = None,
) -> None:
    """
    Processo FIWARE: cliente MQTT persistente (cmds + attrs) e poll da fall SHM.
    """
    global fiware_client, fiware_topic

    configure_logging("fiware")

    if stream_event is not None:
        init_stream_event(stream_event)

    identity = get_device_identity()
    network_settings = get_network_settings()

    device_id = identity.device_id
    broker_host, broker_port, broker_path, use_tls = _mqtt_endpoint(
        network_settings.api_base_url
    )

    fiware_topic = f"/{network_settings.fiware_api_key}/{device_id}/cmd"
    topic_attrs = f"/{network_settings.fiware_api_key}/{device_id}/attrs"

    fiware_client = _create_mqtt_client(broker_path, use_tls)
    fiware_client.connect(host=broker_host, port=broker_port, keepalive=60)
    fiware_client.loop_start()

    fall_shm = attach_fall_shm(fall_shm_name) if fall_shm_name else None
    last_state: str | None = None
    try:
        if fall_shm is None:
            while True:
                time.sleep(0.5)
        else:
            while True:
                event = fall_shm.read_next(timeout=0.05)
                if event is None:
                    continue
                if event.event_type != EVENT_FALL_STATE:
                    continue
                last_state = apply_fall_label(
                    fiware_client, topic_attrs, event.payload, last_state
                )
    finally:
        if fall_shm is not None:
            fall_shm.close()
        fiware_client.loop_stop()
        fiware_client.disconnect()
