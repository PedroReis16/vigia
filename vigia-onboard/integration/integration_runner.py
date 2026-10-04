"""
Processo de integração FIWARE/MQTT do onboard.

Cliente MQTT persistente (cmds + attrs) e poll da fall SHM escrita pelo core.
"""

from __future__ import annotations

import json
import logging
import time
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlparse

import paho.mqtt.client as mqtt
from paho.mqtt.enums import CallbackAPIVersion

from shared.capture_gate import capture_allowed
from shared.event_types import EVENT_FALL_STATE
from shared.fall_ipc import attach_fall_shm, normalize_fall_state
from shared.settings import (
    get_device_identity,
    get_network_settings,
    resolve_ota_dir,
)
from shared.stream_control import set_clips_enabled, set_stream_status

logger = logging.getLogger(__name__)

OTA_DIR = resolve_ota_dir()
PENDING_PATH = OTA_DIR / "pending.json"

_cmd_topic: str | None = None
_device_id: str | None = None

_LOCAL_MQTT_WS_PATH = "/vigia/fiware/mosquitto"
_PROD_MQTT_WS_PATH = "/"


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
    logger.info("Connected to MQTT broker")
    if _cmd_topic:
        client.subscribe(_cmd_topic)


def _on_message(_: mqtt.Client, __: Any, message: mqtt.MQTTMessage) -> None:
    try:
        raw = message.payload.decode()
        logger.info("Message received: %s", raw)
        parsed = _parse_ultralight_command(raw)
        if parsed is None:
            return

        msg_device_id, command, value = parsed
        expected_id = _device_id or get_device_identity().device_id
        if msg_device_id != expected_id:
            return

        match command:
            case "stream_on":
                set_stream_status(True)
            case "stream_off":
                set_stream_status(False)
            case "clips_on":
                set_clips_enabled(True)
            case "clips_off":
                set_clips_enabled(False)
            case "device_update":
                _write_ota_pending(value)
            case _:
                logger.warning("Unknown command: %s", command)
                return
    except Exception as error:
        logger.error("Error parsing message: %s", error)


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
    """
    Porta do Mosquitto WS.

    Em http local a API costuma estar em :8090, mas o broker WebSocket fica
    atrás do Traefik em :81 (`/vigia/fiware/mosquitto`).
    """
    if parsed.scheme == "http":
        if parsed.port in (None, 8090):
            return 81
        return parsed.port
    if parsed.port is not None:
        return parsed.port
    return 443


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
        client_id="vigia-onboard-integration",
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


def _reset_provision_cache() -> None:
    for fn in (get_device_identity, get_network_settings):
        clear = getattr(fn, "cache_clear", None)
        if clear is not None:
            clear()


def _wait_for_provision():
    """Espera identity.json e network.json. Não liga o MQTT antes disso."""
    announced = False
    while True:
        _reset_provision_cache()
        try:
            return get_device_identity(), get_network_settings()
        except FileNotFoundError:
            if not announced:
                logger.info(
                    "Integração à espera de identity.json e network.json"
                )
                announced = True
            time.sleep(0.5)


def run_integration() -> None:
    """
    Processo principal de integração: MQTT persistente + poll da fall SHM.
    """
    global _cmd_topic, _device_id, OTA_DIR, PENDING_PATH

    logger.info("Integration running")

    identity, network_settings = _wait_for_provision()

    OTA_DIR = resolve_ota_dir()
    PENDING_PATH = OTA_DIR / "pending.json"

    _device_id = identity.device_id
    broker_host, broker_port, broker_path, use_tls = _mqtt_endpoint(
        network_settings.api_base_url
    )

    _cmd_topic = f"/{network_settings.fiware_api_key}/{_device_id}/cmd"
    topic_attrs = f"/{network_settings.fiware_api_key}/{_device_id}/attrs"

    client = _create_mqtt_client(broker_path, use_tls)
    client.connect(host=broker_host, port=broker_port, keepalive=60)
    client.loop_start()

    fall_shm = attach_fall_shm()
    try:
        while True:
            if not capture_allowed():
                time.sleep(0.05)
                continue
            event = fall_shm.read_next(timeout=0.05)
            if event is None:
                continue
            if event.event_type != EVENT_FALL_STATE:
                continue
            state = normalize_fall_state(event.payload)
            _publish_fall_state(client, topic_attrs, state)
    except KeyboardInterrupt:
        logger.info("Integration stopped")
    finally:
        fall_shm.close()
        client.loop_stop()
        client.disconnect()
