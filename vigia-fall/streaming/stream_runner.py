"""
Processo dedicado de streaming RTMP — ativo só enquanto stream_on.
"""

from __future__ import annotations

from multiprocessing.synchronize import Event as EventType

from shared import get_stream_status, init_stream_event
from shared.log_config import configure_logging
from streaming.frame_shm import FrameShmRing
from streaming.rtmp import publish_frame, shutdown_stream


def run_stream(
    frame_shm_name: str,
    stream_event: EventType | None = None,
) -> None:
    """
    Consome frames da shared memory e publica via RTMP enquanto o Event estiver setado.
    """
    configure_logging("stream")
    if stream_event is not None:
        init_stream_event(stream_event)

    frame_shm = FrameShmRing.attach(frame_shm_name)
    try:
        while get_stream_status():
            item = frame_shm.read_latest(timeout=0.2)
            if item is None:
                continue
            publish_frame(item.frame, item.stream_fps)
    finally:
        shutdown_stream()
        frame_shm.close()
