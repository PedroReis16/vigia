from __future__ import annotations

import signal
import sys
from multiprocessing import Process

from app.config import Settings, prepare_data_workspace
from app.fiware.device_sync import (
    load_local_device_settings_required,
)
from app.logging import get_logger

from .frame_consumer import run_frame_consumer

logger = get_logger("core")


def run_analysis(settings: Settings) -> None:
    """Prepara diretório de dados e consome frames para análise (pose / quedas)."""
    load_local_device_settings_required()

    prepare_data_workspace(settings, reset=False)

    receive_process = Process(
        target=run_frame_consumer,
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
