"""
Envia um JPEG à API como thumbnail do dispositivo.

POST /devices/{deviceId}/frame
"""

from __future__ import annotations

import logging
import uuid
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin
from urllib.request import Request, urlopen

import cv2  # type: ignore
import numpy as np

from shared.settings import (
    get_device_identity,
    get_identity_path,
    get_network_path,
    get_network_settings,
)

logger = logging.getLogger(__name__)

_JPEG_QUALITY = 70
_HTTP_TIMEOUT_S = 15.0


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


def _post_frame(device_id: str, api_base_url: str, jpeg: bytes) -> None:
    body, content_type = _build_multipart(jpeg)

    url = urljoin(_normalize_api_base(api_base_url), f"devices/{device_id}/frame")
    request = Request(
        url,
        data=body,
        method="POST",
        headers={
            "Content-Type": content_type,
        },
    )

    with urlopen(request, timeout=_HTTP_TIMEOUT_S) as response:
        if response.status < 200 or response.status >= 300:
            raise HTTPError(
                url,
                response.status,
                f"upload de frame retornou {response.status}",
                response.headers,
                None,
            )


def upload_thumbnail(frame: np.ndarray) -> bool:
    """Codifica e envia um JPEG. Devolve False sem levantar se o envio não saiu."""
    if frame is None or frame.size == 0:
        return False

    if not get_identity_path().exists() or not get_network_path().exists():
        return False

    try:
        jpeg = _encode_jpeg(frame)
        if not jpeg:
            logger.warning("Frame uploader: falha ao codificar JPEG")
            return False

        identity = get_device_identity()
        network = get_network_settings()
        _post_frame(identity.device_id, network.api_base_url, jpeg)
        return True
    except (HTTPError, URLError, TimeoutError, ValueError, OSError) as error:
        logger.warning("Frame uploader: erro ao enviar thumbnail: %s", error)
    except Exception as error:  # pylint: disable=broad-exception-caught
        logger.warning("Frame uploader: erro inesperado: %s", error)
    return False
