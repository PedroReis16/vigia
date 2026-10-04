"""
Processo dedicado da janela de clipes — activo só enquanto clips_enabled.

Na entrada em fall, exporta o snapshot em PNG e envia para a API.
"""

from __future__ import annotations

import logging
import threading
import time

from multiprocessing.synchronize import Event as EventType

from shared.clip_frame_shm import ClipFrameRing
from shared.event_shm import EventShmRing
from shared.event_types import EVENT_FALL_STATE
from shared.live_frame_shm import LiveFrameShm
from shared.settings import get_settings
from shared.stream_control import get_clips_enabled
from stream.clip_export import export_fall_clip, next_clip_export

logger = logging.getLogger(__name__)


def _attach_fall_ring(name: str) -> EventShmRing | None:
    try:
        return EventShmRing.attach(name)
    except FileNotFoundError:
        return None


def _latest_fall_state(ring: EventShmRing | None) -> str:
    if ring is None:
        return "normal"
    record = ring.peek_latest()
    if record is None or record.event_type != EVENT_FALL_STATE:
        return "normal"
    return record.payload


def _export_snapshot(frames: list, fps: int) -> None:
    try:
        export_fall_clip(frames, fps)
    except Exception as error:
        logger.warning("Falha ao exportar clipe de queda: %s", error)


def run_clips_worker(
    live_shm_name: str,
    clip_shm_name: str | None = None,
    run_event: EventType | None = None,
) -> None:
    """
    Consome frames da live SHM e empurra para o ClipFrameRing enquanto clips_enabled.

    Na transição para fall, envia a janela numerada para a API sem bloquear o loop.
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
    fall_ring = _attach_fall_ring(settings.fall_shm_name)
    in_episode = False
    export_thread: threading.Thread | None = None
    try:
        while True:
            if run_event is not None:
                if not run_event.is_set():
                    break
            elif not get_clips_enabled():
                break
            if fall_ring is None:
                fall_ring = _attach_fall_ring(settings.fall_shm_name)
            item = live_shm.read_latest(timeout=0.2)
            if item is not None:
                clip_shm.push(item.frame, capture_ts=time.monotonic())

            busy = export_thread is not None and export_thread.is_alive()
            export, in_episode = next_clip_export(
                in_episode,
                _latest_fall_state(fall_ring),
                len(clip_shm),
                busy,
            )
            if not export:
                continue
            frames = [clip.frame for clip in clip_shm.snapshot()]
            if not frames:
                in_episode = False
                continue
            export_thread = threading.Thread(
                target=_export_snapshot,
                args=(frames, settings.frame_rate),
                name="clip-export",
                daemon=True,
            )
            export_thread.start()
        logger.info("Clips worker a encerrar")
    finally:
        clip_shm.close()
        live_shm.close()
        if fall_ring is not None:
            fall_ring.close()
        logger.info("Clips worker terminado")
