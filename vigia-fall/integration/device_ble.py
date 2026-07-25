import asyncio
import base64
import json
import os
from typing import Any, Optional
from uuid import UUID
from bless import BlessServer
from bless.backends.attribute import GATTAttributePermissions
from bless.backends.characteristic import (
    BlessGATTCharacteristic,
    GATTCharacteristicProperties,
)
from cryptography.hazmat.primitives.asymmetric import ed25519, x25519
from cryptography.hazmat.primitives import serialization

server: BlessServer = None
loop: Optional[asyncio.AbstractEventLoop] = None

SERVICE_UUID = "adbb2064-403f-490f-8e0b-d2df7a3e8976"
CHAR_IDENTITY_UUID = "776ee4be-ecd4-4331-9f0e-7a53f1d9a4ba"  # Read
CHAR_CHALLENGE_UUID = "2984802e-d12e-4e6c-870f-3b37f1845961"  # Read | Write
CHAR_PROVISION_UUID = "2562213c-2180-4320-a70f-247a6125b47a"  # Write

session_key: Optional[bytes] = None
device_context: dict[str, UUID] = {}

def __write_request(characteristic: BlessGATTCharacteristic, value: Any, **kwargs):
    global device_context

    if characteristic.uuid == CHAR_CHALLENGE_UUID:
        print("Escrevendo resposta do desafio de sincronia...")
        try:
            app_signature = bytes.fromhex(value.hex())

            # Verifica se a assinatura do app é válida comparando com o nonce gerado pelo dispositivo
            # celular_pub_key.verify(app_signature, device_context["current_nonce"])

            device_context["authenticated_session"] = True
            characteristic.value = b"VALIDATED"
        except Exception:
            device_context["authenticated_session"] = False
            characteristic.value = b"INVALID"

    elif characteristic.uuid == CHAR_PROVISION_UUID:
        print("Escrevendo resposta do provisionamento de rede...")

        if not device_context["authenticated_session"]:
            characteristic.value = b"UNAUTHORIZED"
            return

        try:
            payload = json.loads(value.decode("utf-8"))

            # Captura os dados enviados pelo seu aplicativo mobile
            wifi_ssid = payload.get("ssid") # Nome da rede WiFi para a conexão do dispositivo
            wifi_password = payload.get("password") # Senha da rede WiFi para a conexão do dispositivo

            api_token_confirmation = payload.get(
                "api_token"
            )  # Confirmação de vínculo com a API

            # 1. Salvar dados de conexão no banco de dados
            # 2. Disparar a rotina para conectar o dispositivo à rede WiFi

            characteristic.value = b"SUCCESS"
        except Exception as e:
            characteristic.value = b"ERROR_PAYLOAD"


def __read_identity() -> bytearray:
    """
    Tratamento da requisição de captura dos dados de identificação para sincronia entre dispositivo e usuário
    """
    global device_context

    pub_sign = (
        device_context["sign_priv"]
        .public_key()
        .public_bytes(
            encoding=serialization.Encoding.Raw, format=serialization.PublicFormat.Raw
        )
        .hex()
    )

    pub_ecdh = (
        device_context["ecdh_priv"]
        .public_key()
        .public_bytes(
            encoding=serialization.Encoding.Raw, format=serialization.PublicFormat.Raw
        )
        .hex()
    )

    identity_packet = {
        "device_id": str(device_context["device_id"]),
        "sign_pub": pub_sign,
        "ecdh_pub": pub_ecdh,
    }

    return bytearray(json.dumps(identity_packet).encode("utf-8"))


def __read_challenge() -> bytearray:
    """
    Tratamento da requisição da captura do desafio de sincronia entre dispositivo e usuário
    para confirmação de identifidade e permissão de acesso ao dispositivo embarcado
    """
    global device_context

    device_context["current_nonce"] = os.urandom(16)
    return bytearray(device_context["current_nonce"].hex().encode("utf-8"))


def __read_request(characteristic: BlessGATTCharacteristic, **kwargs) -> bytearray:
    """
    Lê o valor da characteristic.
    """
    print(f"Lendo requisição da characteristic: {characteristic.uuid}")

    # Primeiro vínculo -> App lê os dados de identidade para mandar para a API
    if characteristic.uuid == CHAR_IDENTITY_UUID:
        print("Lendo dados de identidade...")
        data = __read_identity()
        characteristic.value = data
        return data
    # Etapa de desafio -> Para conexões futuras -> Gera um número aleatório único para o app assinar
    if characteristic.uuid == CHAR_CHALLENGE_UUID:
        data = __read_challenge()
        characteristic.value = data
        return data

    return characteristic.value


async def init_register_beacon(
    device_id: UUID,
    device_name: str,
    sign_priv: ed25519.Ed25519PrivateKey,
    ecdh_priv: x25519.X25519PrivateKey,
) -> None:
    """
    Inicialização do beacon do dispositivo para conexão via Bluetooth
    """
    global server, loop, device_context
    loop = asyncio.get_event_loop()
    server = BlessServer(device_name, loop=loop)

    device_context = {
        "device_id": device_id,
        "sign_priv": sign_priv,
        "ecdh_priv": ecdh_priv,
    }

    server.read_request_func = __read_request
    server.write_request_func = __write_request

    # Adiciona o serviço customizado principal
    await server.add_new_service(SERVICE_UUID)

    # Característica: Device ID (Apenas leitura)
    await server.add_new_characteristic(
        SERVICE_UUID,
        CHAR_IDENTITY_UUID,
        GATTCharacteristicProperties.read,
        None,
        GATTAttributePermissions.readable,
    )

    # Característica: Handshake (Leitura e Escrita)
    await server.add_new_characteristic(
        SERVICE_UUID,
        CHAR_CHALLENGE_UUID,
        GATTCharacteristicProperties.read | GATTCharacteristicProperties.write,
        None,
        GATTAttributePermissions.readable | GATTAttributePermissions.writeable,
    )

    # Característica: Provisionamento de rede (Escrita) -> Captura das redes disponíveis para o dispositivo

    await server.add_new_characteristic(
        SERVICE_UUID,
        CHAR_PROVISION_UUID,
        GATTCharacteristicProperties.write,
        None,
        GATTAttributePermissions.writeable,
    )

    await server.start()

    seconds = 0

    while True:
        await asyncio.sleep(1)
        seconds += 1
        print(f"Tempo de espera: {seconds} segundos")

    # while seconds < 60:
    #     await asyncio.sleep(1)
    #     seconds += 1

    # await server.stop()
    # print("Beacon de registro do dispositivo embarcado com bluetooth encerrado...")
    # raise Exception("Timeout de conexão com o dispositivo embarcado com bluetooth")