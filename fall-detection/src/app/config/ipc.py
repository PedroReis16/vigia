"""Contrato de transporte de frames entre processos (ZMQ IPC)."""

from __future__ import annotations

import zmq

# Publicado em ``app.capture.loop``; consumido por core, streaming, etc.
FRAMES_IPC_URL = "ipc:///tmp/frames.ipc"
FRAMES_TOPIC = b"frame"


def bind_frame_pub_socket(socket: zmq.Socket) -> None:
    socket.bind(FRAMES_IPC_URL)


def configure_frame_sub_socket(socket: zmq.Socket) -> None:
    socket.connect(FRAMES_IPC_URL)
    socket.setsockopt(zmq.SUBSCRIBE, FRAMES_TOPIC)
    socket.setsockopt(zmq.CONFLATE, 1)
