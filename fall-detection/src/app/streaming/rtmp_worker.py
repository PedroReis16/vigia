"""Worker: lê frames do IPC (ZMQ SUB) e envia para RTMP via FFmpeg."""

from __future__ import annotations

import pickle

import numpy as np
import zmq

from app.config.ipc import configure_frame_sub_socket
from app.logging import get_logger
from app.streaming.stream_video import stream_video

logger = get_logger("streaming.rtmp")


def run_rtmp_worker(rtmp_url: str) -> None:
    context = zmq.Context()
    socket = context.socket(zmq.SUB)
    configure_frame_sub_socket(socket)

    try:
        while True:
            _, payload = socket.recv_multipart()
            frame = pickle.loads(payload)
            frame = np.array(frame)
            stream_video(frame, rtmp_url)
    except KeyboardInterrupt:
        pass
    except Exception as e:
        logger.error("erro ao transmitir frame: {}", e)
        raise
    finally:
        socket.close()
        context.term()
