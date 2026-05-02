from __future__ import annotations
import datetime
import pickle
import signal
import sys
import time
from multiprocessing import Process

import cv2
import numpy as np
import schedule
import zmq

from app.config import Settings
from app.fiware.device_sync import load_local_device_settings_required
from app.logging import get_logger
from app.streaming.stream_video import stream_video

logger = get_logger("streaming")

def _consume_frames(rtmp_url: str)-> None:

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
       

            stream_video(frame, rtmp_url)
    except KeyboardInterrupt:
        pass
    except Exception as e:
        logger.error(f"erro ao transmitir frame: {e}")
        raise
    finally:
        socket.close()
        context.term()

def _consume_monitor()-> None:
    try:
        now = datetime.datetime.now()
        print(f"monitorando consumo de frames. {now}")
    except Exception as e:
        logger.warning("Limite de recursos atingido, encerrando streaming")


def run_streaming(settings: Settings) -> None:
    """Inicia o streaming de vídeo do que esta sendo capturado pela camera"""
    device_settings = load_local_device_settings_required()

    rtmp_url = settings.stream_ingest_url.rstrip("/")

    rtmp_url = f"{rtmp_url}/{device_settings.device_id}"

    stream_process = Process(
        target=_consume_frames,
        args=(rtmp_url,),
        daemon=True,
    )
    stream_process.start()

    def _shutdown_stream_tree(*_args: object) -> None:
        """SIGTERM do processo pai (via command_bus): encerra o filho que faz RTMP/ZMQ."""
        if stream_process.is_alive():
            stream_process.terminate()
            stream_process.join(timeout=10)
            if stream_process.is_alive():
                stream_process.kill()
                stream_process.join(timeout=5)
        sys.exit(0)

    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, _shutdown_stream_tree)
    if hasattr(signal, "SIGINT"):
        signal.signal(signal.SIGINT, _shutdown_stream_tree)

    schedule.every(3).seconds.do(_consume_monitor)

    while True:
        try:
            while True:
                schedule.run_pending()

                if not stream_process.is_alive():
                    break
                
        except Exception as e:
            print(f"erro ao monitorar consumo de frames: {e}")
            break
        finally:
            stream_process.terminate()
            stream_process.join()
            logger.info("streaming finalizado")
            break

    stream_process.join()
    logger.info("streaming finalizado")

