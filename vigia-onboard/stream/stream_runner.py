"""
Processo dedicado de streaming RTMP — ativo só enquanto stream_on.
"""

from __future__ import annotations

import logging
import time

from multiprocessing.synchronize import Event as EventType

from shared.live_frame_shm import LiveFrameShm
from shared.stream_control import get_stream_on
from stream.rtmp import publish_frame, shutdown_stream

logger = logging.getLogger(__name__)


def run_stream_worker(live_shm_name: str, run_event: EventType | None = None) -> None:
    """
    Consome frames da live SHM e publica via FFmpeg/RTMP enquanto ``run_event`` estiver setado.

    O ciclo de vida vem do Event do processo pai (não de um poll que pode
    divergir e fazer o filho sair e ser recriado no hot path da captura).
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s [stream] %(message)s",
    )
    logger.info("Stream worker iniciado (live=%s)", live_shm_name)
    frame_shm = LiveFrameShm.attach(live_shm_name)
    try:
        while True:
            if run_event is not None:
                if not run_event.is_set():
                    break
            elif not get_stream_on():
                break
            item = frame_shm.read_latest(timeout=0.2)
            if item is None:
                continue
            if not publish_frame(item.frame, item.stream_fps):
                if run_event is not None:
                    run_event.clear()
                break
        logger.info("Stream worker a encerrar")
    finally:
        shutdown_stream()
        frame_shm.close()
        logger.info("Stream worker terminado")


def idle_until_stream_off(*, poll_s: float = 0.1) -> None:
    """Espera stream_on ficar false (utilitário de teste / diagnóstico)."""
    while get_stream_on():
        time.sleep(poll_s)
