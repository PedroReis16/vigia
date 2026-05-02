from __future__ import annotations
import pickle
from app.config import Settings
from app.logging import get_logger
from app.fiware.device_sync import load_local_device_settings_required
from app.streaming.stream_video import stream_video

import zmq
import cv2
import numpy as np

logger = get_logger("streaming")

def run_streaming(settings: Settings) -> None:
    """Inicia o streaming de vídeo do que esta sendo capturado pela camera"""
    
    load_local_device_settings_required()

    context = zmq.Context()
    socket = context.socket(zmq.SUB)
    socket.connect("ipc:///tmp/frames.ipc")
    socket.setsockopt(zmq.SUBSCRIBE, b"frame")

    # Mantém apenas o frame mais recente - descarta os intermediários
    socket.setsockopt(zmq.CONFLATE, 1)

    try:
        while True:
            _, payload = socket.recv_multipart()


            frame = pickle.loads(payload)
            frame = np.array(frame)
       

            stream_video(frame)
    except KeyboardInterrupt:
        pass
    finally:
        socket.close()
        context.term()