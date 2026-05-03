from __future__ import annotations
from multiprocessing import Process
import pickle
import signal
import sys
import time

from app.config import Settings, prepare_data_workspace
from app.fiware.device_sync import (
    load_local_device_settings_required,
)
from app.logging import get_logger
import zmq
import numpy as np

logger = get_logger("core")


def _consume_frames()-> None:
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


            print("frame recebido")
    except KeyboardInterrupt:
        pass
    except Exception as e:
        logger.error(f"erro ao consumir frames: {e}")
    finally:
        socket.close()
        context.term()


def run_analysis(settings: Settings) -> None:
    """Prepara diretório de dados e executa modelos de postura / quedas."""
    load_local_device_settings_required()

    prepare_data_workspace(settings, reset=False)

    receive_process = Process(
        target=_consume_frames,
        daemon=True,
    )
    receive_process.start()

    def _shutdown_stream_tree(*_args: object) -> None:
        """SIGTERM do processo pai (via command_bus): encerra o filho que faz RTMP/ZMQ."""
        if receive_process.is_alive():
            receive_process.terminate()
            receive_process.join(timeout=10)
            if receive_process.is_alive():
                receive_process.kill()
                receive_process.join(timeout=5)
            sys.exit(0)

    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, _shutdown_stream_tree)
    if hasattr(signal, "SIGINT"):
        signal.signal(signal.SIGINT, _shutdown_stream_tree)

    receive_process.join()

    logger.info("processo de analise em execucao")
