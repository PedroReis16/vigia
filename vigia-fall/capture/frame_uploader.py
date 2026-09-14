"""
Envia frames JPEG periódicos à API como thumbnail do dispositivo.

POST /devices/{deviceId}/frame com DeviceSignature (Ed25519), alinhado a
seed-codes/publish_frame.py e DeviceSignatureAuthentication.

Canonical (API DeviceSignatureAuthenticationHandler):
  POST\\n/devices/{deviceId}/frame\\n{unix_ts}\\n{sha256_hex(raw_body)}

Path assinado é sem PathBase (/vigia). Em DEBUG, identity do device seedado
deve usar shared.test_device_seed.SIGN_PRIVATE_KEY (derivada; ver get_device_identity).
"""

from __future__ import annotations

import hashlib
import logging
import threading
import time
import uuid
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin
from urllib.request import Request, urlopen

import cv2  # pyright: ignore[reportMissingImports]
import numpy as np
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from shared import (
    get_device_identity,
    get_identity_path,
    get_network_path,
    get_network_settings,
)

logger = logging.getLogger(__name__)

# Frame cache TTL na API é 120s — renovar antes de expirar.
_UPLOAD_INTERVAL_S = 60.0
_JPEG_QUALITY = 70
_HTTP_TIMEOUT_S = 15.0

_lock = threading.Lock()
_last_upload_monotonic = 0.0
_upload_in_flight = False


def _normalize_api_base(api_base_url: str) -> str:
    return api_base_url if api_base_url.endswith("/") else f"{api_base_url}/"


def _build_multipart(jpeg: bytes, field_name: str = "frameFile") -> tuple[bytes, str]:
    boundary = f"----VigiaBoundary{uuid.uuid4().hex}"
    body = b"".join(
        [
            f"--{boundary}\r\n".encode(),
            (
                f'Content-Disposition: form-data; name="{field_name}"; '
                f'filename="frame.jpg"\r\n'
                f"Content-Type: image/jpeg\r\n\r\n"
            ).encode(),
            jpeg,
            b"\r\n",
            f"--{boundary}--\r\n".encode(),
        ]
    )
    return body, f"multipart/form-data; boundary={boundary}"


def _encode_jpeg(frame: np.ndarray) -> bytes | None:
    ok, encoded = cv2.imencode(
        ".jpg",
        frame,
        [int(cv2.IMWRITE_JPEG_QUALITY), _JPEG_QUALITY],
    )
    if not ok:
        return None
    return encoded.tobytes()


def _sign_and_post(device_id: str, sign_priv_hex: str, api_base_url: str, jpeg: bytes) -> None:
    private_key = Ed25519PrivateKey.from_private_bytes(bytes.fromhex(sign_priv_hex))
    body, content_type = _build_multipart(jpeg)

    timestamp = int(time.time())
    body_hash = hashlib.sha256(body).hexdigest()
    canonical = f"POST\n/devices/{device_id}/frame\n{timestamp}\n{body_hash}"
    signature_hex = private_key.sign(canonical.encode("utf-8")).hex()

    url = urljoin(_normalize_api_base(api_base_url), f"devices/{device_id}/frame")
    request = Request(
        url,
        data=body,
        method="POST",
        headers={
            "Content-Type": content_type,
            "X-Device-Timestamp": str(timestamp),
            "X-Device-Signature": signature_hex,
        },
    )

    with urlopen(request, timeout=_HTTP_TIMEOUT_S) as response:
        # 202 Accepted esperado; outros 2xx também ok.
        if response.status < 200 or response.status >= 300:
            raise HTTPError(
                url,
                response.status,
                f"upload de frame retornou {response.status}",
                response.headers,
                None,
            )


def _upload_worker(frame: np.ndarray) -> None:
    global _last_upload_monotonic, _upload_in_flight

    try:
        jpeg = _encode_jpeg(frame)
        if not jpeg:
            logger.warning("Frame uploader: falha ao codificar JPEG")
            return

        identity = get_device_identity()
        network = get_network_settings()
        _sign_and_post(
            identity.device_id,
            identity.sign_priv,
            network.api_base_url,
            jpeg,
        )
        with _lock:
            _last_upload_monotonic = time.monotonic()
    except (HTTPError, URLError, TimeoutError, ValueError, OSError) as error:
        logger.warning("Frame uploader: erro ao enviar thumbnail: %s", error)
    except Exception as error:  # pylint: disable=broad-exception-caught
        logger.warning("Frame uploader: erro inesperado: %s", error)
    finally:
        with _lock:
            _upload_in_flight = False


def maybe_upload_thumbnail(frame: np.ndarray) -> None:
    """
    Enfileira upload de thumbnail se o intervalo mínimo já passou.

    Não bloqueia o loop de captura; no máximo um upload em voo.
    """
    global _upload_in_flight

    if frame is None or frame.size == 0:
        return

    if not get_identity_path().exists() or not get_network_path().exists():
        return

    now = time.monotonic()
    with _lock:
        if _upload_in_flight:
            return
        if now - _last_upload_monotonic < _UPLOAD_INTERVAL_S:
            return
        _upload_in_flight = True

    threading.Thread(
        target=_upload_worker,
        args=(frame.copy(),),
        name="frame-uploader",
        daemon=True,
    ).start()
