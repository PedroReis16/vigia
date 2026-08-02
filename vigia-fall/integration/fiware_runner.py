"""
Módulo para controle e inicialização da integração entre o dispositivo e o FIWARE
"""

import json
from urllib.parse import urlparse
import paho.mqtt.client as mqtt
from paho.mqtt.enums import CallbackAPIVersion


from shared import get_device_identity, get_network_settings


fiware_client: mqtt.Client = None
fiware_topic: str = None


def _on_connect(client, userdata, flags, reason_code, properties=None):
    global fiware_client, fiware_topic

    print("Connected to MQTT broker")
    client.subscribe(fiware_topic)


def _on_message(client, userdata, message):
    try:
        # payload = json.loads(message.payload.decode())

        print(f"Message received")
        # TODO: Realizar o processamento dos dados recebidos

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


def run_fiware():
    """
    Executa a rotina principal do FIWARE para recebimento de dados do dispositivo.
    """
    global fiware_client, fiware_topic

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
