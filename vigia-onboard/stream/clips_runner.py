"""
Processo dedicado da janela de clipes — activo só enquanto clips_enabled.

Na entrada em fall, exporta o snapshot em PNG e envia para a API.
"""

from __future__ import annotations

import logging
import threading
import time

import numpy as np
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


def clip_frame_size(
    height: int, width: int, channels: int, max_payload: int
) -> tuple[int, int]:
    """Tamanho (altura, largura) que cabe em ``max_payload`` bytes."""
    if height < 1 or width < 1 or channels < 1 or max_payload < channels:
        return height, width
    if height * width * channels <= max_payload:
        return height, width

    scale = (max_payload / (height * width * channels)) ** 0.5
    new_w = max(1, int(width * scale))
    new_h = max(1, int(height * scale))
    while new_w * new_h * channels > max_payload and (new_w > 1 or new_h > 1):
        if new_w >= new_h and new_w > 1:
            new_w -= 1
        elif new_h > 1:
            new_h -= 1
        else:
            break
    return new_h, new_w


def encode_clip_jpeg(frame: np.ndarray, max_payload: int) -> bytes | None:
    """JPEG na resolução da câmera. Qualidade 100; só baixa se não couber no slot."""
    import cv2

    for quality in (100, 95, 90, 85, 80, 70):
        ok, buf = cv2.imencode(".jpg", frame, [1, quality])
        if not ok:
            continue
        payload = buf.tobytes()
        if len(payload) <= max_payload:
            return payload
    return None


def _store_clip_frame(clip_shm: ClipFrameRing, frame: np.ndarray) -> None:
    """Guarda o frame no ring. JPEG no processo de clips se o cru não cabe."""
    limit = clip_shm.max_payload
    if not isinstance(limit, int) or frame.nbytes <= limit:
        clip_shm.push(frame, capture_ts=time.monotonic())
        return
    encoded = encode_clip_jpeg(frame, limit)
    if encoded is not None:
        height, width = int(frame.shape[0]), int(frame.shape[1])
        clip_shm.push_jpeg(encoded, width, height, capture_ts=time.monotonic())
        return
    clip_shm.push(fit_frame_to_payload(frame, limit), capture_ts=time.monotonic())


def fit_frame_to_payload(frame: np.ndarray, max_payload: int) -> np.ndarray:
    """Reduz o frame até caber em ``max_payload`` bytes, mantendo a proporção."""
    height, width = int(frame.shape[0]), int(frame.shape[1])
    channels = 1 if frame.ndim == 2 else int(frame.shape[2])
    new_h, new_w = clip_frame_size(height, width, channels, max_payload)
    if new_h == height and new_w == width:
        return frame

    import cv2

    return cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_AREA)


def _resolve_clip_fps(capture_fps: int | None, fallback: int) -> int:
    """FPS da câmera para a janela e o MP4. Sem leitura da fonte, usa FRAME_RATE."""
    if capture_fps is not None and int(capture_fps) > 0:
        return max(1, int(capture_fps))
    return max(1, int(fallback))


def run_clips_worker(
    live_shm_name: str,
    clip_shm_name: str | None = None,
    run_event: EventType | None = None,
    capture_fps: int | None = None,
) -> None:
    """
    Consome frames da live SHM e empurra para o ClipFrameRing enquanto clips_enabled.

    A janela cabe ``CLIP_WINDOW_S`` no fps da câmera (o mesmo do stream). Na
    transição para fall, envia a janela numerada para a API sem bloquear o loop.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s [clips] %(message)s",
    )
    settings = get_settings()
    clip_name = (clip_shm_name or settings.clip_shm_name).strip() or settings.clip_shm_name
    playback_fps = _resolve_clip_fps(capture_fps, settings.frame_rate)
    slot_count = settings.clip_slots_for(playback_fps)
    logger.info(
        "Clips worker iniciado (live=%s clip=%s slots=%s fps=%s)",
        live_shm_name,
        clip_name,
        slot_count,
        playback_fps,
    )
    live_shm = LiveFrameShm.attach(live_shm_name)
    clip_shm = ClipFrameRing.open_or_create(
        clip_name,
        slot_count=slot_count,
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
                if item.stream_fps > 0:
                    playback_fps = int(item.stream_fps)
                _store_clip_frame(clip_shm, item.frame)

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
                args=(frames, playback_fps),
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
