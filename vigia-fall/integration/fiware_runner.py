"""
Módulo para controle e inicialização da integração entre o dispositivo e o FIWARE
"""

from typing import Any
from urllib.parse import urlparse
from multiprocessing.synchronize import Event as EventType
import paho.mqtt.client as mqtt
from paho.mqtt.enums import CallbackAPIVersion


from shared import (
    get_device_identity,
    get_network_settings,
    init_stream_event,
    set_stream_status,
)



import json
import os
from datetime import datetime, timezone
from pathlib import Path as _Path

OTA_DIR = _Path(os.getenv("VIGIA_OTA_DIR", "/var/lib/vigia/ota"))
PENDING_PATH = OTA_DIR / "pending.json"


def _write_ota_pending(version: str) -> None:
    version = (version or "").strip()
    if not version:
        print("device_update sem versao — ignorado")
        return
    OTA_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "version": version,
        "received_at": datetime.now(timezone.utc).isoformat(),
    }
    PENDING_PATH.write_text(json.dumps(payload), encoding="utf-8")
    print(f"OTA pending escrito: {version}")


def _parse_ultralight_command(payload: str) -> tuple[str, str, str] | None:
    parts = payload.split("@", 1)
    if len(parts) != 2:
        return None
    device_id = parts[0]
    command, _, value = parts[1].partition("|")
    return device_id, command.strip(), value.strip()


fiware_client: mqtt.Client = None
fiware_topic: str = None


def _on_connect(
    client: mqtt.Client,
    _: Any,
    __: Any,
    ___: Any,
    ____: Any,
) -> None:
    """
    Callback para conexão com o broker MQTT
    """
    print("Connected to MQTT broker")
    client.subscribe(fiware_topic)


def _on_message(_: mqtt.Client, __: Any, message: mqtt.MQTTMessage) -> None:
    """
    Callback para recebimento de mensagens do FIWARE
    """
    try:
        raw = message.payload.decode()
        print(f"Message received: {raw}")
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
                print(f"Unknown command: {command}")
                return

    except Exception as e:
        print(f"Error parsing message: {e}")
        return



def _mqtt_endpoint(api_base_url: str) -> tuple[str, int]:
    parsed = urlparse(api_base_url)
    if not parsed.hostname:
        raise ValueError(f"URL inválida: {api_base_url}")
    host = parsed.hostname
    port = 443 if parsed.scheme == "https" else 81
    return host, port


def run_fiware(stream_event: EventType | None = None):
    """
    Executa a rotina principal do FIWARE para recebimento de dados do dispositivo.
    """
    global fiware_client, fiware_topic

    if stream_event is not None:
        init_stream_event(stream_event)

    identity = get_device_identity()
    network_settings = get_network_settings()

    device_id = identity.device_id
    broker_host, broker_port = _mqtt_endpoint(network_settings.api_base_url)

    fiware_topic = f"/{network_settings.fiware_api_key}/{device_id}/cmd"

    fiware_client = mqtt.Client(
        callback_api_version=CallbackAPIVersion.VERSION2,
        client_id="vigia-consumer",
        transport="websockets",
    )
    fiware_client.ws_set_options(path="/vigia/fiware/mosquitto")
    fiware_client.on_connect = _on_connect
    fiware_client.on_message = _on_message

    fiware_client.connect(host=broker_host, port=broker_port, keepalive=60)

    fiware_client.loop_forever()
