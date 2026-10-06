"""
Exporta a janela de clipes quando o estado entra em queda.

Os frames saem em PNG sem perdas (ffmpeg) e seguem para a API sem assinatura.
"""

from __future__ import annotations

import json
import logging
import subprocess
import tempfile
import uuid
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin
from urllib.request import Request, urlopen

import numpy as np

from shared.fall_ipc import normalize_fall_state
from shared.settings import get_device_identity, get_network_settings
from stream.rtmp import _ffmpeg_executable, _system_subprocess_env

logger = logging.getLogger(__name__)

_HTTP_TIMEOUT_S = 30.0
_UPLOAD_WORKERS = 4


def next_clip_export(
    in_episode: bool,
    state: str,
    frame_count: int,
    export_busy: bool,
) -> tuple[bool, bool]:
    """
    Decide se esta leitura deve disparar um clipe.

    Devolve ``(exportar, em_episodio)``. A entrada em ``fall`` exporta uma vez;
    ``fall`` repetido não. Sair de ``fall`` liberta o episódio. Ring vazio ou
    export em curso não dispara outro envio.
    """
    is_fall = normalize_fall_state(state) == "fall"
    if not is_fall:
        return False, False
    if in_episode or export_busy:
        return False, True
    if frame_count <= 0:
        return False, False
    return True, True


def encode_frames_as_png(frames: list[np.ndarray], dest_dir: Path) -> list[Path]:
    """Codifica frames BGR num PNG numerado ``000000.png`` via um processo ffmpeg."""
    if not frames:
        return []

    images = [np.ascontiguousarray(frame) for frame in frames]
    shape = images[0].shape
    if any(image.ndim != 3 or image.shape[2] != 3 or image.shape != shape for image in images):
        raise ValueError("os frames do clipe precisam ser BGR e ter o mesmo tamanho")

    height, width = shape[:2]
    dest_dir.mkdir(parents=True, exist_ok=True)
    raw_path = dest_dir / "frames.raw"
    pattern = str(dest_dir / "%06d.png")
    command = [
        _ffmpeg_executable(),
        "-y",
        "-hide_banner",
        "-loglevel",
        "error",
        "-f",
        "rawvideo",
        "-pix_fmt",
        "bgr24",
        "-s",
        f"{width}x{height}",
        "-i",
        str(raw_path),
        "-start_number",
        "0",
        pattern,
    ]
    with raw_path.open("wb") as handle:
        for image in images:
            handle.write(image.tobytes())
    try:
        completed = subprocess.run(
            command,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            env=_system_subprocess_env(),
            check=False,
        )
        if completed.returncode != 0:
            detail = completed.stderr.decode("utf-8", errors="replace").strip()
            raise RuntimeError(f"ffmpeg PNG saiu com {completed.returncode}: {detail}")
    finally:
        raw_path.unlink(missing_ok=True)

    return sorted(path for path in dest_dir.glob("*.png") if path.stem.isdigit())


def upload_clip(
    api_base_url: str,
    device_id: str,
    clip_id: str,
    fps: int,
    frames: list[Path],
    *,
    opener: Callable[..., object] = urlopen,
) -> None:
    """Abre a sessão e envia os PNG em paralelo, cada um no seu índice."""
    if not frames:
        return

    base = api_base_url if api_base_url.endswith("/") else f"{api_base_url}/"
    session_url = urljoin(base, f"devices/{device_id}/clips")
    session_body = json.dumps(
        {"clipId": clip_id, "frameCount": len(frames), "fps": max(1, int(fps))}
    ).encode("utf-8")
    _post(opener, session_url, session_body, "application/json")

    def send(item: tuple[int, Path]) -> None:
        index, path = item
        frame_url = urljoin(base, f"devices/{device_id}/clips/{clip_id}/frames/{index}")
        _post(opener, frame_url, path.read_bytes(), "image/png")

    workers = max(1, min(_UPLOAD_WORKERS, len(frames)))
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(send, item) for item in enumerate(frames)]
        for future in futures:
            future.result()


def export_fall_clip(frames: list[np.ndarray], fps: int) -> None:
    """Comprime o snapshot e publica o clipe na API."""
    if not frames:
        return

    identity = get_device_identity()
    network = get_network_settings()
    clip_id = str(uuid.uuid4())
    with tempfile.TemporaryDirectory(prefix="vigia-clip-") as tmp:
        paths = encode_frames_as_png(frames, Path(tmp))
        if not paths:
            return
        upload_clip(
            network.api_base_url,
            identity.device_id,
            clip_id,
            fps,
            paths,
        )
    logger.info("Clipe %s enviado (%s frames)", clip_id, len(frames))


def _post(opener: Callable[..., object], url: str, body: bytes, content_type: str) -> None:
    request = Request(
        url,
        data=body,
        method="POST",
        headers={"Content-Type": content_type},
    )
    try:
        response = opener(request, timeout=_HTTP_TIMEOUT_S)
    except (HTTPError, URLError, TimeoutError, OSError):
        raise
    close = getattr(response, "close", None)
    status = getattr(response, "status", None)
    if status is None:
        status = getattr(response, "code", 200)
    try:
        if int(status) < 200 or int(status) >= 300:
            raise HTTPError(url, int(status), f"upload de clipe retornou {status}", None, None)
    finally:
        if callable(close):
            close()
