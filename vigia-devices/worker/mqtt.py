"""Cliente MQTT Ultralight (cmds stream_on/off + attrs fall)."""

from __future__ import annotations

import logging
import threading
from typing import Any
from urllib.parse import urlparse

import paho.mqtt.client as mqtt
from paho.mqtt.enums import CallbackAPIVersion

logger = logging.getLogger(__name__)

_LOCAL_MQTT_WS_PATH = "/vigia/fiware/mosquitto"
_PROD_MQTT_WS_PATH = "/"


def mqtt_host(parsed) -> str:
    hostname = parsed.hostname or ""
    if parsed.scheme == "http":
        return hostname
    labels = hostname.split(".")
    if len(labels) >= 3:
        labels[0] = "mosquitto"
        return ".".join(labels)
    return f"mosquitto.{hostname}"


def mqtt_port(parsed) -> int:
    if parsed.scheme == "http":
        if parsed.port in (None, 8090):
            return 81
        return parsed.port
    if parsed.port is not None:
        return parsed.port
    return 443


def mqtt_ws_path(parsed) -> str:
    return _LOCAL_MQTT_WS_PATH if parsed.scheme == "http" else _PROD_MQTT_WS_PATH


def mqtt_endpoint(api_base_url: str) -> tuple[str, int, str, bool]:
    parsed = urlparse(api_base_url)
    if not parsed.hostname:
        raise ValueError(f"URL inválida: {api_base_url}")
    host = mqtt_host(parsed)
    port = mqtt_port(parsed)
    path = mqtt_ws_path(parsed)
    use_tls = parsed.scheme == "https"
    return host, port, path, use_tls


def parse_ultralight_command(payload: str) -> tuple[str, str, str] | None:
    parts = payload.split("@", 1)
    if len(parts) != 2:
        return None
    device_id = parts[0]
    command, _, value = parts[1].partition("|")
    return device_id, command.strip(), value.strip()


class MqttBridge:
    """Mantém ligação MQTT e aplica stream_on/off no Event partilhado."""

    def __init__(
        self,
        *,
        api_base_url: str,
        fiware_api_key: str,
        device_id: str,
        stream_on: threading.Event,
    ) -> None:
        self._device_id = device_id
        self._stream_on = stream_on
        self._api_key = fiware_api_key
        self._host, self._port, self._path, self._use_tls = mqtt_endpoint(api_base_url)
        self._cmd_topic = f"/{fiware_api_key}/{device_id}/cmd"
        self._attrs_topic = f"/{fiware_api_key}/{device_id}/attrs"
        self._client: mqtt.Client | None = None
        self._lock = threading.Lock()
        self._last_fall: str | None = None

    @property
    def attrs_topic(self) -> str:
        return self._attrs_topic

    def start(self) -> None:
        client = mqtt.Client(
            callback_api_version=CallbackAPIVersion.VERSION2,
            client_id=f"vigia-devices-{self._device_id[:8]}",
            transport="websockets",
        )
        client.ws_set_options(path=self._path)
        if self._use_tls:
            client.tls_set()
        client.on_connect = self._on_connect
        client.on_message = self._on_message
        logger.info(
            "MQTT a ligar %s:%s%s (device=%s)",
            self._host,
            self._port,
            self._path,
            self._device_id,
        )
        client.connect(host=self._host, port=self._port, keepalive=60)
        client.loop_start()
        self._client = client

    def stop(self) -> None:
        client = self._client
        self._client = None
        if client is None:
            return
        client.loop_stop()
        client.disconnect()

    def publish_fall(self, state: str) -> None:
        """Publica ``fall|{state}`` se o estado mudou."""
        normalized = (state or "").strip().lower()
        if normalized not in {"normal", "suspect", "fall", "false_positive"}:
            raise ValueError(f"fall state inválido: {state}")
        with self._lock:
            if normalized == self._last_fall:
                return
            self._last_fall = normalized
        client = self._client
        if client is None:
            logger.warning("MQTT não ligado — fall|%s ignorado", normalized)
            return
        client.publish(self._attrs_topic, f"fall|{normalized}")
        logger.info("Publicado fall|%s", normalized)

    def _on_connect(
        self,
        client: mqtt.Client,
        _: Any,
        __: Any,
        ___: Any,
        ____: Any,
    ) -> None:
        logger.info("MQTT ligado")
        client.subscribe(self._cmd_topic)

    def _on_message(self, _: mqtt.Client, __: Any, message: mqtt.MQTTMessage) -> None:
        try:
            raw = message.payload.decode()
            parsed = parse_ultralight_command(raw)
            if parsed is None:
                return
            msg_device_id, command, _value = parsed
            if msg_device_id != self._device_id:
                return
            if command == "stream_on":
                self._stream_on.set()
                logger.info("cmd stream_on")
            elif command == "stream_off":
                self._stream_on.clear()
                logger.info("cmd stream_off")
            else:
                logger.debug("cmd ignorado: %s", command)
        except Exception as exc:  # pylint: disable=broad-exception-caught
            logger.warning("Erro ao processar MQTT: %s", exc)
