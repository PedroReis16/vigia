"""Beacon BLE de provisionamento de rede (identidade e Wi-Fi)."""

from __future__ import annotations

import asyncio
import json
import logging
import threading
from typing import TYPE_CHECKING, Any, Optional
from urllib.parse import urlparse
from uuid import UUID

from . import state
from .settings import get_settings
from .wifi import connect_and_persist

if TYPE_CHECKING:
    from bless import BlessServer
    from bless.backends.characteristic import BlessGATTCharacteristic

log = logging.getLogger(__name__)

server: Optional["BlessServer"] = None
loop: Optional[asyncio.AbstractEventLoop] = None

SERVICE_UUID = "adbb2064-403f-490f-8e0b-d2df7a3e8976"
CHAR_IDENTITY_UUID = "776ee4be-ecd4-4331-9f0e-7a53f1d9a4ba"
CHAR_PROVISION_UUID = "2562213c-2180-4320-a70f-247a6125b47a"

device_context: dict = {}


def _bless_import_ok() -> bool:
    try:
        import bless  # noqa: F401
    except ImportError:
        return False
    return True


def is_ble_available() -> bool:
    """True quando BLE está activo e a stack bless pode ser carregada."""
    if not get_settings().ble_enabled:
        return False
    return _bless_import_ok()


def ble_unavailable_reason() -> str:
    if not get_settings().ble_enabled:
        return "BLE desativado (BLE_ENABLED=false)"
    return "BLE indisponível (dependência bless em falta — necessária só no deploy)"


def _load_bless():
    from bless import BlessServer
    from bless.backends.attribute import GATTAttributePermissions
    from bless.backends.characteristic import (
        BlessGATTCharacteristic,
        GATTCharacteristicProperties,
    )

    return (
        BlessServer,
        GATTAttributePermissions,
        BlessGATTCharacteristic,
        GATTCharacteristicProperties,
    )


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


def __set_provision_status(
    status: bytes, characteristic: Optional["BlessGATTCharacteristic"] = None
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
    characteristic: Optional["BlessGATTCharacteristic"],
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


def __write_request(characteristic: "BlessGATTCharacteristic", value: Any):
    global device_context

    if __uuid_eq(characteristic.uuid, CHAR_PROVISION_UUID):
        log.info("Escrevendo resposta do provisionamento de rede...")

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
    identity_packet = {
        "device_id": str(device_context["device_id"]),
        "name": device_context["device_name"],
        "mac_address": device_context["mac_address"],
    }

    return bytearray(json.dumps(identity_packet).encode("utf-8"))


def __read_request(characteristic: "BlessGATTCharacteristic") -> bytearray:
    if __uuid_eq(characteristic.uuid, CHAR_IDENTITY_UUID):
        data = __read_identity()
        characteristic.value = data
        state.set_pairing_stage(state.APP_CONNECTED)
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
    cancel: Optional[threading.Event] = None,
) -> None:
    global server, loop, device_context

    if not is_ble_available():
        raise RuntimeError(ble_unavailable_reason())

    (
        BlessServer,
        GATTAttributePermissions,
        _BlessGATTCharacteristic,
        GATTCharacteristicProperties,
    ) = _load_bless()
    loop = asyncio.get_event_loop()
    server = BlessServer(device_name, loop=loop)

    device_context = {
        "device_id": device_id,
        "device_name": device_name,
        "mac_address": mac_address,
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
