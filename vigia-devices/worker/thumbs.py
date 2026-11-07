"""Upload periódico de thumbnail JPEG."""

from __future__ import annotations

import logging
import threading
import uuid
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin
from urllib.request import Request, urlopen

import cv2  # type: ignore
import numpy as np

from worker.frame_bus import FrameBus

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


def encode_jpeg(frame: np.ndarray) -> bytes | None:
    ok, encoded = cv2.imencode(
        ".jpg",
        frame,
        [int(cv2.IMWRITE_JPEG_QUALITY), _JPEG_QUALITY],
    )
    if not ok:
        return None
    return encoded.tobytes()


def upload_thumbnail(api_base_url: str, device_id: str, frame: np.ndarray) -> bool:
    jpeg = encode_jpeg(frame)
    if not jpeg:
        logger.warning("Falha ao codificar JPEG da thumbnail")
        return False

    body, content_type = _build_multipart(jpeg)
    url = urljoin(_normalize_api_base(api_base_url), f"devices/{device_id}/frame")
    request = Request(
        url,
        data=body,
        method="POST",
        headers={"Content-Type": content_type},
    )
    try:
        with urlopen(request, timeout=_HTTP_TIMEOUT_S) as response:
            if response.status < 200 or response.status >= 300:
                raise HTTPError(
                    url,
                    response.status,
                    f"upload de frame retornou {response.status}",
                    response.headers,
                    None,
                )
        return True
    except (HTTPError, URLError, TimeoutError, OSError) as exc:
        logger.warning("Thumbnail falhou: %s", exc)
        return False


def run_thumbs_loop(
    bus: FrameBus,
    stop_event: threading.Event,
    *,
    api_base_url: str,
    device_id: str,
    interval_s: float,
) -> None:
    """Envia thumbnail a cada ``interval_s`` (e uma vez assim que houver frame)."""
    first_sent = False
    while not stop_event.is_set():
        frame = bus.latest()
        if frame is not None:
            if upload_thumbnail(api_base_url, device_id, frame):
                if not first_sent:
                    logger.info("Primeira thumbnail enviada")
                    first_sent = True
            wait = interval_s if first_sent else min(5.0, interval_s)
        else:
            wait = 1.0
        stop_event.wait(wait)
