"""Upload de clipe PNG (contrato DevicesClipController)."""

from __future__ import annotations

import logging
import tempfile
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin
from urllib.request import Request, urlopen

import cv2  # type: ignore
import numpy as np

logger = logging.getLogger(__name__)

MAX_FRAME_COUNT = 4096
_HTTP_TIMEOUT_S = 60.0
_PARALLEL_UPLOADS = 4


def _normalize_api_base(api_base_url: str) -> str:
    return api_base_url if api_base_url.endswith("/") else f"{api_base_url}/"


def _http_json(url: str, payload: bytes, content_type: str) -> None:
    request = Request(
        url,
        data=payload,
        method="POST",
        headers={"Content-Type": content_type},
    )
    with urlopen(request, timeout=_HTTP_TIMEOUT_S) as response:
        if response.status < 200 or response.status >= 300:
            raise HTTPError(
                url,
                response.status,
                f"HTTP {response.status}",
                response.headers,
                None,
            )


def encode_png_frames(frames: list[np.ndarray], dest: Path) -> list[Path]:
    dest.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    for index, frame in enumerate(frames):
        ok, encoded = cv2.imencode(".png", frame)
        if not ok:
            raise RuntimeError(f"Falha ao codificar PNG do frame {index}")
        path = dest / f"{index:06d}.png"
        path.write_bytes(encoded.tobytes())
        paths.append(path)
    return paths


def upload_clip_session(
    api_base_url: str,
    device_id: str,
    frames: list[np.ndarray],
    *,
    fps: int,
    clip_id: str | None = None,
) -> str:
    """Abre a sessão de clipe e envia cada PNG. Devolve o clipId."""
    if not frames:
        raise ValueError("Sem frames para o clipe")
    if len(frames) > MAX_FRAME_COUNT:
        raise ValueError(
            f"Clipe com {len(frames)} frames excede o máximo {MAX_FRAME_COUNT}"
        )

    clip = clip_id or str(uuid.uuid4())
    fps_i = max(1, int(fps))
    base = _normalize_api_base(api_base_url)

    import json

    session_body = json.dumps(
        {"clipId": clip, "frameCount": len(frames), "fps": fps_i}
    ).encode("utf-8")
    session_url = urljoin(base, f"devices/{device_id}/clips")
    _http_json(session_url, session_body, "application/json")

    with tempfile.TemporaryDirectory(prefix="vigia-clip-") as tmp:
        paths = encode_png_frames(frames, Path(tmp))

        def _upload_one(index_path: tuple[int, Path]) -> None:
            index, path = index_path
            frame_url = urljoin(
                base, f"devices/{device_id}/clips/{clip}/frames/{index}"
            )
            data = path.read_bytes()
            request = Request(
                frame_url,
                data=data,
                method="POST",
                headers={"Content-Type": "image/png"},
            )
            with urlopen(request, timeout=_HTTP_TIMEOUT_S) as response:
                if response.status < 200 or response.status >= 300:
                    raise HTTPError(
                        frame_url,
                        response.status,
                        f"HTTP {response.status}",
                        response.headers,
                        None,
                    )

        with ThreadPoolExecutor(max_workers=_PARALLEL_UPLOADS) as pool:
            futures = [
                pool.submit(_upload_one, (index, path))
                for index, path in enumerate(paths)
            ]
            for future in as_completed(futures):
                future.result()

    logger.info("Clipe %s enviado (%s frames @ %sfps)", clip, len(frames), fps_i)
    return clip


def upload_clip_from_bus_frames(
    api_base_url: str,
    device_id: str,
    frames: list[np.ndarray],
    fps: float,
) -> str | None:
    """Wrapper que engole erros de rede e devolve None em falha."""
    if not frames:
        logger.warning("Buffer de clipe vazio — skip")
        return None
    try:
        return upload_clip_session(
            api_base_url,
            device_id,
            frames,
            fps=max(1, int(round(fps))),
        )
    except (HTTPError, URLError, TimeoutError, OSError, RuntimeError, ValueError) as exc:
        logger.warning("Upload de clipe falhou: %s", exc)
        return None
