"""Consumo de frames publicados pelo loop de captura (ZMQ SUB)."""

from __future__ import annotations

import pickle

import numpy as np
import zmq

from app.config.ipc import configure_frame_sub_socket
from app.logging import get_logger

logger = get_logger("frame_consumer")


def run_frame_consumer() -> None:
    context = zmq.Context()
    socket = context.socket(zmq.SUB)
    configure_frame_sub_socket(socket)

    try:
        while True:
            _, payload = socket.recv_multipart()
            frame = pickle.loads(payload)
            frame = np.array(frame)
            print("frame recebido")
    except KeyboardInterrupt:
        pass
    except Exception as e:
        logger.error("erro ao consumir frames: {}", e)
    finally:
        socket.close()
        context.term()
