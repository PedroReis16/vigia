"""
Implementação do BLE para o dispositivo
"""

import asyncio
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
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519, x25519

server: BlessServer = None
loop: Optional[asyncio.AbstractEventLoop] = None

SERVICE_UUID = "adbb2064-403f-490f-8e0b-d2df7a3e8976"
CHAR_IDENTITY_UUID = "776ee4be-ecd4-4331-9f0e-7a53f1d9a4ba"  # Read
CHAR_CHALLENGE_UUID = "2984802e-d12e-4e6c-870f-3b37f1845961"  # Read | Write
CHAR_PROVISION_UUID = "2562213c-2180-4320-a70f-247a6125b47a"  # Write

_STATUS_VALIDATED = b"VALIDATED"
_STATUS_INVALID = b"INVALID"

session_key: Optional[bytes] = None
device_context: dict = {}


def __uuid_eq(left: Any, right: str) -> bool:
    return str(left).lower() == right.lower()


def __as_bytes(value: Any) -> bytes:
    if isinstance(value, memoryview):
        return value.tobytes()
    if isinstance(value, bytearray):
        return bytes(value)
    if isinstance(value, bytes):
        return value
    return bytes(value)


def __write_request(characteristic: BlessGATTCharacteristic, value: Any):
    global device_context 

    if __uuid_eq(characteristic.uuid, CHAR_CHALLENGE_UUID):
        print("Escrevendo resposta do desafio de sincronia...")
        try:
            payload = json.loads(__as_bytes(value).decode("utf-8"))
            signature_hex = payload.get("signature")
            if not signature_hex:
                raise ValueError("signature ausente")

            nonce = device_context.get("current_nonce")
            if not nonce:
                raise ValueError("nenhum desafio ativo")

            stored_pub = device_context.get("app_sign_pub")
            incoming_pub = payload.get("app_sign_pub")

            if stored_pub:
                pub_hex = stored_pub
            elif incoming_pub:
                pub_hex = incoming_pub
                device_context["app_sign_pub"] = incoming_pub
            else:
                raise ValueError("app_sign_pub ausente no primeiro vínculo")

            public_key = ed25519.Ed25519PublicKey.from_public_bytes(
                bytes.fromhex(pub_hex)
            )
            public_key.verify(bytes.fromhex(signature_hex), nonce)

            device_context["authenticated_session"] = True
            device_context["last_challenge_status"] = _STATUS_VALIDATED
            characteristic.value = bytearray(_STATUS_VALIDATED)
            print("Desafio VALIDATED")
        except (InvalidSignature, ValueError, KeyError, json.JSONDecodeError) as exc:
            print(f"Desafio INVALID: {exc}")
            device_context["authenticated_session"] = False
            device_context["last_challenge_status"] = _STATUS_INVALID
            characteristic.value = bytearray(_STATUS_INVALID)
        except Exception as exc:
            print(f"Desafio INVALID (erro inesperado): {exc}")
            device_context["authenticated_session"] = False
            device_context["last_challenge_status"] = _STATUS_INVALID
            characteristic.value = bytearray(_STATUS_INVALID)

    elif __uuid_eq(characteristic.uuid, CHAR_PROVISION_UUID):
        print("Escrevendo resposta do provisionamento de rede...")

        if not device_context.get("authenticated_session"):
            device_context["last_provision_status"] = b"UNAUTHORIZED"
            characteristic.value = bytearray(b"UNAUTHORIZED")
            return

        try:
            payload = json.loads(__as_bytes(value).decode("utf-8"))

            wifi_ssid = payload.get("ssid")
            wifi_password = payload.get("password")
            api_token_confirmation = payload.get("api_token")

            if not wifi_ssid or wifi_password is None or not api_token_confirmation:
                raise ValueError("payload incompleto")

            device_context["wifi_ssid"] = wifi_ssid
            device_context["wifi_password"] = wifi_password
            device_context["api_token"] = api_token_confirmation

            # TODO: persistir credenciais e conectar à rede Wi‑Fi
            print(
                f"Provision recebido: ssid={wifi_ssid!r}, "
                f"api_token={api_token_confirmation!r}"
            )

            device_context["last_provision_status"] = b"SUCCESS"
            characteristic.value = bytearray(b"SUCCESS")
        except Exception as exc:
            print(f"Provision ERROR_PAYLOAD: {exc}")
            device_context["last_provision_status"] = b"ERROR_PAYLOAD"
            characteristic.value = bytearray(b"ERROR_PAYLOAD")


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
    Gera um nonce único para o app assinar (confirmação de identidade).
    """
    global device_context 

    device_context["current_nonce"] = os.urandom(16)
    device_context["authenticated_session"] = False
    return bytearray(device_context["current_nonce"].hex().encode("utf-8"))


def __read_request(characteristic: BlessGATTCharacteristic) -> bytearray:
    """
    Lê o valor da characteristic.
    """
    if __uuid_eq(characteristic.uuid, CHAR_IDENTITY_UUID):
        data = __read_identity()
        characteristic.value = data
        return data

    if __uuid_eq(characteristic.uuid, CHAR_CHALLENGE_UUID):
        status = device_context.pop("last_challenge_status", None)
        if status is not None:
            characteristic.value = bytearray(status)
            return bytearray(status)

        data = __read_challenge()
        characteristic.value = data
        return data

    if __uuid_eq(characteristic.uuid, CHAR_PROVISION_UUID):
        status = device_context.pop("last_provision_status", None)
        if status is not None:
            characteristic.value = bytearray(status)
            return bytearray(status)
        return bytearray(characteristic.value or b"")

    return bytearray(characteristic.value or b"")


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
        "authenticated_session": False,
        "app_sign_pub": None,
    }

    server.read_request_func = __read_request
    server.write_request_func = __write_request

    await server.add_new_service(SERVICE_UUID)

    await server.add_new_characteristic(
        SERVICE_UUID,
        CHAR_IDENTITY_UUID,
        GATTCharacteristicProperties.read,
        None,
        GATTAttributePermissions.readable,
    )

    await server.add_new_characteristic(
        SERVICE_UUID,
        CHAR_CHALLENGE_UUID,
        GATTCharacteristicProperties.read | GATTCharacteristicProperties.write,
        None,
        GATTAttributePermissions.readable | GATTAttributePermissions.writeable,
    )

    await server.add_new_characteristic(
        SERVICE_UUID,
        CHAR_PROVISION_UUID,
        GATTCharacteristicProperties.write | GATTCharacteristicProperties.read,
        None,
        GATTAttributePermissions.writeable | GATTAttributePermissions.readable,
    )

    await server.start()

    seconds = 0

    while True:
        await asyncio.sleep(1)
        seconds += 1
        print(f"Tempo de espera: {seconds} segundos")
