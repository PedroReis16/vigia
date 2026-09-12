"""Beacon BLE de provisionamento (mesmo protocolo GATT do fall)."""

from __future__ import annotations

import asyncio
import base64
import binascii
import json
import logging
import os
import threading
from typing import Any, Optional
from urllib.parse import urlparse
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

from . import state
from .wifi import connect_and_persist

log = logging.getLogger(__name__)

server: Optional[BlessServer] = None
loop: Optional[asyncio.AbstractEventLoop] = None

SERVICE_UUID = "adbb2064-403f-490f-8e0b-d2df7a3e8976"
CHAR_IDENTITY_UUID = "776ee4be-ecd4-4331-9f0e-7a53f1d9a4ba"
CHAR_CHALLENGE_UUID = "2984802e-d12e-4e6c-870f-3b37f1845961"
CHAR_PROVISION_UUID = "2562213c-2180-4320-a70f-247a6125b47a"

_STATUS_VALIDATED = b"VALIDATED"
_STATUS_INVALID = b"INVALID"

device_context: dict = {}


def _legacy_stream_ingest_url(api_base_url: str) -> str:
    """Calcula o ingest para payloads enviados por apps antigos."""
    parsed = urlparse((api_base_url or "").strip())
    if not parsed.hostname:
        raise ValueError("api_base_url inválida")

    if parsed.scheme == "http":
        return f"rtmp://{parsed.hostname}:1935"

    if parsed.scheme == "https":
        hostname = parsed.hostname
        if hostname.startswith("services."):
            hostname = f"ingest.{hostname.removeprefix('services.')}"
        else:
            hostname = f"ingest.{hostname}"
        return f"rtmps://{hostname}:8443"

    raise ValueError("api_base_url deve usar http ou https")


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


def _decode_ed25519_field(value: str, expected_len: int) -> bytes:
    """Decode hex (legacy) or base64 (compact BLE write) Ed25519 material."""
    normalized = value.strip()
    if len(normalized) == expected_len * 2 and all(
        ch in "0123456789abcdefABCDEF" for ch in normalized
    ):
        return bytes.fromhex(normalized)
    try:
        decoded = base64.b64decode(normalized, validate=True)
    except binascii.Error as exc:
        raise ValueError("campo Ed25519 inválido") from exc
    if len(decoded) != expected_len:
        raise ValueError("campo Ed25519 inválido")
    return decoded


def _parse_auth_payload(payload: dict[str, Any]) -> tuple[bytes, bytes]:
    signature_raw = payload.get("signature")
    if not signature_raw:
        raise ValueError("signature ausente")

    incoming_pub = payload.get("app_sign_pub")
    if not incoming_pub:
        raise ValueError("app_sign_pub ausente no primeiro vínculo")

    pub_bytes = _decode_ed25519_field(str(incoming_pub), 32)
    sig_bytes = _decode_ed25519_field(str(signature_raw), 64)
    return pub_bytes, sig_bytes


def __set_provision_status(
    status: bytes, characteristic: Optional[BlessGATTCharacteristic] = None
) -> None:
    device_context["last_provision_status"] = status
    target = characteristic or device_context.get("provision_characteristic")
    if target is not None:
        target.value = bytearray(status)


async def __provision_wifi_async(
    ssid: str,
    password: str,
    api_base_url: str,
    fiware_api_key: str,
    stream_ingest_url: str,
    characteristic: Optional[BlessGATTCharacteristic],
) -> None:
    try:
        await connect_and_persist(
            ssid,
            password,
            api_base_url,
            fiware_api_key,
            stream_ingest_url=stream_ingest_url,
        )
        __set_provision_status(b"SUCCESS", characteristic)
        state.set_pairing_stage(state.WIFI_OK)
        device_context["stop_beacon"] = True
        log.info("Provision SUCCESS: Wi‑Fi conectado")
    except Exception as exc:
        log.warning("Provision WIFI_FAIL: %s", exc)
        __set_provision_status(b"WIFI_FAIL", characteristic)
        state.set_pairing_stage(state.WIFI_FAIL)


def __write_request(characteristic: BlessGATTCharacteristic, value: Any):
    global device_context

    if __uuid_eq(characteristic.uuid, CHAR_CHALLENGE_UUID):
        log.info("Escrevendo resposta do desafio de sincronia...")
        try:
            payload = json.loads(__as_bytes(value).decode("utf-8"))
            pub_bytes, sig_bytes = _parse_auth_payload(payload)

            nonce = device_context.get("current_nonce")
            if not nonce:
                raise ValueError("nenhum desafio ativo")

            pub_hex = pub_bytes.hex()
            stored_pub = device_context.get("app_sign_pub")
            if stored_pub:
                if stored_pub != pub_hex:
                    raise ValueError("app_sign_pub divergente")
            else:
                device_context["app_sign_pub"] = pub_hex

            public_key = ed25519.Ed25519PublicKey.from_public_bytes(pub_bytes)
            public_key.verify(sig_bytes, nonce)

            device_context["authenticated_session"] = True
            device_context["last_challenge_status"] = _STATUS_VALIDATED
            characteristic.value = bytearray(_STATUS_VALIDATED)
            state.set_pairing_stage(state.USER_FOUND)
            log.info("Desafio VALIDATED")
        except (InvalidSignature, ValueError, KeyError, json.JSONDecodeError) as exc:
            log.warning("Desafio INVALID: %s", exc)
            device_context["authenticated_session"] = False
            device_context["last_challenge_status"] = _STATUS_INVALID
            characteristic.value = bytearray(_STATUS_INVALID)
            state.set_pairing_stage(state.PAIRING_ERROR)
        except Exception as exc:
            log.warning("Desafio INVALID (erro inesperado): %s", exc)
            device_context["authenticated_session"] = False
            device_context["last_challenge_status"] = _STATUS_INVALID
            characteristic.value = bytearray(_STATUS_INVALID)
            state.set_pairing_stage(state.PAIRING_ERROR)

    elif __uuid_eq(characteristic.uuid, CHAR_PROVISION_UUID):
        log.info("Escrevendo resposta do provisionamento de rede...")

        if not device_context.get("authenticated_session"):
            __set_provision_status(b"UNAUTHORIZED", characteristic)
            state.set_pairing_stage(state.PAIRING_ERROR)
            return

        try:
            payload = json.loads(__as_bytes(value).decode("utf-8"))

            wifi_ssid = payload.get("ssid")
            wifi_password = payload.get("password") or payload.get("pass")
            api_base_url = (
                payload.get("api_base_url")
                or payload.get("api_token")
                or payload.get("api")
            )
            fiware_api_key = payload.get("fiware_api_key") or payload.get("fiware")
            stream_ingest_url = str(payload.get("stream_ingest_url") or "").strip()
            if not stream_ingest_url:
                stream_ingest_url = _legacy_stream_ingest_url(api_base_url)
                log.warning(
                    "Payload sem stream_ingest_url; usando fallback de compatibilidade: %s",
                    stream_ingest_url,
                )

            if (
                not wifi_ssid
                or wifi_password is None
                or not api_base_url
                or not stream_ingest_url
            ):
                raise ValueError("payload incompleto")

            device_context["provision_characteristic"] = characteristic
            __set_provision_status(b"CONNECTING", characteristic)
            state.set_pairing_stage(state.WIFI_CONNECTING)

            log.info(
                "Provision recebido: ssid=%r, api_base_url=%r",
                wifi_ssid,
                api_base_url,
            )

            active_loop = loop or asyncio.get_event_loop()
            active_loop.create_task(
                __provision_wifi_async(
                    wifi_ssid,
                    wifi_password,
                    api_base_url,
                    fiware_api_key,
                    stream_ingest_url,
                    characteristic,
                )
            )
        except Exception as exc:
            log.warning("Provision ERROR_PAYLOAD: %s", exc)
            __set_provision_status(b"ERROR_PAYLOAD", characteristic)
            state.set_pairing_stage(state.PAIRING_ERROR)


def __read_identity() -> bytearray:
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
        "name": device_context["device_name"],
        "mac_address": device_context["mac_address"],
        "sign_pub": pub_sign,
        "ecdh_pub": pub_ecdh,
    }

    return bytearray(json.dumps(identity_packet).encode("utf-8"))


def __read_challenge() -> bytearray:
    device_context["current_nonce"] = os.urandom(16)
    device_context["authenticated_session"] = False
    return bytearray(device_context["current_nonce"].hex().encode("utf-8"))


def __read_request(characteristic: BlessGATTCharacteristic) -> bytearray:
    if __uuid_eq(characteristic.uuid, CHAR_IDENTITY_UUID):
        data = __read_identity()
        characteristic.value = data
        state.set_pairing_stage(state.APP_CONNECTED)
        return data

    if __uuid_eq(characteristic.uuid, CHAR_CHALLENGE_UUID):
        status = device_context.pop("last_challenge_status", None)
        if status is not None:
            if status == _STATUS_VALIDATED:
                state.set_pairing_stage(state.WAITING_WIFI)
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
    mac_address: str,
    sign_priv: ed25519.Ed25519PrivateKey,
    ecdh_priv: x25519.X25519PrivateKey,
    cancel: Optional[threading.Event] = None,
) -> None:
    global server, loop, device_context
    loop = asyncio.get_event_loop()
    server = BlessServer(device_name, loop=loop)

    device_context = {
        "device_id": device_id,
        "device_name": device_name,
        "mac_address": mac_address,
        "sign_priv": sign_priv,
        "ecdh_priv": ecdh_priv,
        "authenticated_session": False,
        "app_sign_pub": None,
        "stop_beacon": False,
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
    log.info("Beacon BLE iniciado (%s)", device_name)

    seconds = 0
    cancelled = False
    while not device_context.get("stop_beacon"):
        if cancel is not None and cancel.is_set():
            cancelled = True
            break
        await asyncio.sleep(1)
        seconds += 1
        log.info("Tempo de espera: %s segundos", seconds)

    if not cancelled:
        await asyncio.sleep(15)

    try:
        await server.stop()
    except Exception as exc:
        log.warning("Falha ao encerrar beacon BLE: %s", exc)

    if cancelled:
        log.info("Beacon BLE encerrado (reset / cancelamento)")
    else:
        log.info("Beacon BLE encerrado após provisionamento")
