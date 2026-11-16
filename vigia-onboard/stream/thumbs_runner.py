"""
Processo dedicado de thumbnails.

Lê o último frame da live SHM e envia um JPEG à API a cada 60s.
"""

from __future__ import annotations

import logging
import time

from multiprocessing.synchronize import Event as EventType

from shared.live_frame_shm import LiveFrameShm
from stream.frame_uploader import upload_thumbnail

logger = logging.getLogger(__name__)

# Frame cache TTL na API é 120s — renovar antes de expirar.
_UPLOAD_INTERVAL_S = 60.0
_RETRY_S = 5.0
_POLL_S = 0.2


def _still_running(run_event: EventType | None) -> bool:
    return run_event is None or run_event.is_set()


def run_thumbs_worker(
    live_shm_name: str,
    run_event: EventType | None = None,
) -> None:
    """
    Consome o frame mais recente da live SHM e publica a thumbnail.

    O ciclo de vida vem do Event do processo pai, como o stream e os clipes.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s [thumbs] %(message)s",
    )
    logger.info("Thumbs worker iniciado (live=%s)", live_shm_name)
    frame_shm = LiveFrameShm.attach(live_shm_name)
    last_upload: float | None = None
    try:
        while _still_running(run_event):
            now = time.monotonic()
            if last_upload is not None and now - last_upload < _UPLOAD_INTERVAL_S:
                time.sleep(_POLL_S)
                continue

            item = frame_shm.read_latest(timeout=_POLL_S)
            if item is None:
                continue

            if upload_thumbnail(item.frame):
                last_upload = time.monotonic()
            else:
                last_upload = time.monotonic() - (_UPLOAD_INTERVAL_S - _RETRY_S)

        logger.info("Thumbs worker a encerrar")
    finally:
        frame_shm.close()
        logger.info("Thumbs worker terminado")
