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
        print(f"Message received: {message.payload.decode()}")
        message_parts = message.payload.decode().split("@")

        if (
            len(message_parts) == 0
            or message_parts[0] != get_device_identity().device_id
        ):
            return

        command = message_parts[1].replace("|", "")

        match command:
            case "stream_on":
                set_stream_status(True)
            case "stream_off":
                set_stream_status(False)
            case _:
                print(f"Unknown command: {message_parts[1]}")
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
