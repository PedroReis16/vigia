#!/usr/bin/env python3
"""Worker mock de dispositivos Vigia — stream RTMP, thumbnail, queda + clipe."""

from __future__ import annotations

import logging
import random
import signal
import sys
import threading

from worker.claim import wait_and_claim
from worker.fall_sim import run_fall_sim_loop
from worker.frame_bus import FrameBus
from worker.mqtt import MqttBridge
from worker.playback import run_playback
from worker.rtmp import run_rtmp_loop
from worker.settings import list_videos, load_device_pool, load_settings
from worker.thumbs import run_thumbs_loop

logger = logging.getLogger("vigia-devices")


def _configure_logging(level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level, logging.INFO),
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
        datefmt="%H:%M:%S",
    )


def main() -> int:
    settings = load_settings()
    _configure_logging(settings.log_level)

    videos = list_videos(settings.assets_dir)
    if not videos:
        logger.error(
            "Nenhum vídeo em %s — coloque pelo menos um .mp4 (ver assets/videos/README.md)",
            settings.assets_dir,
        )
        return 1

    pool = load_device_pool(settings.pool_path)
    stop_event = threading.Event()

    def _handle_signal(_signum, _frame) -> None:
        logger.info("Sinal de paragem recebido")
        stop_event.set()

    signal.signal(signal.SIGINT, _handle_signal)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, _handle_signal)

    logger.info("A claimar device do pool (%s slots)...", len(pool))
    try:
        claim = wait_and_claim(
            settings.redis_url,
            pool,
            device_id=settings.device_id,
            ttl_s=settings.claim_ttl_s,
            stop_event=stop_event,
        )
    except (RuntimeError, ValueError) as exc:
        logger.error("%s", exc)
        return 1

    device = claim.device
    video = random.choice(videos)
    logger.info(
        "Worker ativo: %s (%s) vídeo=%s",
        device.name,
        device.id,
        video.name,
    )

    bus = FrameBus(clip_window_s=settings.clip_window_s)
    stream_on = threading.Event()
    mqtt = MqttBridge(
        api_base_url=settings.api_base_url,
        fiware_api_key=settings.fiware_api_key,
        device_id=device.id,
        stream_on=stream_on,
    )

    threads: list[threading.Thread] = []

    def _spawn(name: str, target, *args, **kwargs) -> None:
        thread = threading.Thread(
            target=target,
            args=args,
            kwargs=kwargs,
            name=name,
            daemon=True,
        )
        threads.append(thread)
        thread.start()

    try:
        mqtt.start()
        _spawn("playback", run_playback, video, bus, stop_event)
        _spawn(
            "rtmp",
            run_rtmp_loop,
            bus,
            stream_on,
            stop_event,
            stream_ingest_url=settings.stream_ingest_url,
            device_id=device.id,
        )
        _spawn(
            "thumbs",
            run_thumbs_loop,
            bus,
            stop_event,
            api_base_url=settings.api_base_url,
            device_id=device.id,
            interval_s=settings.thumb_interval_s,
        )
        _spawn(
            "fall-sim",
            run_fall_sim_loop,
            mqtt,
            bus,
            stop_event,
            api_base_url=settings.api_base_url,
            device_id=device.id,
            fall_min_s=settings.fall_min_s,
            fall_max_s=settings.fall_max_s,
        )

        while not stop_event.wait(1.0):
            pass
    except Exception as exc:  # pylint: disable=broad-exception-caught
        logger.exception("Worker falhou: %s", exc)
        stop_event.set()
        return 1
    finally:
        stop_event.set()
        mqtt.stop()
        claim.release()
        for thread in threads:
            thread.join(timeout=3)

    logger.info("Worker encerrado")
    return 0


if __name__ == "__main__":
    sys.exit(main())
