"""
Processo dedicado de streaming RTMP — ativo só enquanto stream_on.
"""

from __future__ import annotations

from multiprocessing.queues import Queue as MpQueue
from multiprocessing.synchronize import Event as EventType

from shared import get_stream_status, init_stream_event
from shared.log_config import configure_logging
from streaming.frame_ipc import get_frame
from streaming.rtmp import shutdown_stream, stream_video


def run_stream(
    frame_queue: MpQueue,
    stream_event: EventType | None = None,
) -> None:
    """
    Consome frames da Queue IPC e publica via RTMP enquanto o Event estiver setado.
    """
    configure_logging("stream")
    if stream_event is not None:
        init_stream_event(stream_event)

    try:
        while get_stream_status():
            frame = get_frame(frame_queue, timeout=0.2)
            if frame is None:
                continue
            stream_video(frame)
    finally:
        shutdown_stream()
