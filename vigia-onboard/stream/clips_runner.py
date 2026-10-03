"""
Processo dedicado da janela de clipes — activo só enquanto clips_enabled.
"""

from __future__ import annotations

import logging
import time

from multiprocessing.synchronize import Event as EventType

from shared.clip_frame_shm import ClipFrameRing
from shared.live_frame_shm import LiveFrameShm
from shared.settings import get_settings
from shared.stream_control import get_clips_enabled

logger = logging.getLogger(__name__)


def run_clips_worker(
    live_shm_name: str,
    clip_shm_name: str | None = None,
    run_event: EventType | None = None,
) -> None:
    """
    Consome frames da live SHM e empurra para o ClipFrameRing enquanto clips_enabled.

    Nesta entrega não exporta nem envia frames; só mantém a janela deslizante.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s [clips] %(message)s",
    )
    settings = get_settings()
    clip_name = (clip_shm_name or settings.clip_shm_name).strip() or settings.clip_shm_name
    logger.info(
        "Clips worker iniciado (live=%s clip=%s slots=%s)",
        live_shm_name,
        clip_name,
        settings.clip_slot_count,
    )
    live_shm = LiveFrameShm.attach(live_shm_name)
    clip_shm = ClipFrameRing.open_or_create(
        clip_name,
        slot_count=settings.clip_slot_count,
        max_payload=settings.clip_max_payload,
    )
    try:
        while True:
            if run_event is not None:
                if not run_event.is_set():
                    break
            elif not get_clips_enabled():
                break
            item = live_shm.read_latest(timeout=0.2)
            if item is None:
                continue
            clip_shm.push(item.frame, capture_ts=time.monotonic())
        logger.info("Clips worker a encerrar")
    finally:
        clip_shm.close()
        live_shm.close()
        logger.info("Clips worker terminado")
