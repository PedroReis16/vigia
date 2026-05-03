from __future__ import annotations

import signal
import sys
import time
from multiprocessing import Process

import schedule

from app.config import Settings
from app.fiware.device_sync import load_local_device_settings_required
from app.logging import get_logger

from .monitor import log_streaming_tick
from .rtmp_worker import run_rtmp_worker

logger = get_logger("streaming")

_MONITOR_INTERVAL_SECONDS = 3
_SCHEDULE_POLL_SECONDS = 0.5


def run_streaming(settings: Settings) -> None:
    """Inicia o streaming de vídeo do que está a ser capturado pela câmera."""
    device_settings = load_local_device_settings_required()

    base = settings.stream_ingest_url.rstrip("/")
    rtmp_url = f"{base}/{device_settings.device_id}"

    stream_process = Process(
        target=run_rtmp_worker,
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

    schedule.every(_MONITOR_INTERVAL_SECONDS).seconds.do(log_streaming_tick)

    try:
        while stream_process.is_alive():
            schedule.run_pending()
            time.sleep(_SCHEDULE_POLL_SECONDS)
    except KeyboardInterrupt:
        pass
    finally:
        if stream_process.is_alive():
            stream_process.terminate()
            stream_process.join(timeout=10)
            if stream_process.is_alive():
                stream_process.kill()
                stream_process.join(timeout=5)
        logger.info("streaming finalizado")
