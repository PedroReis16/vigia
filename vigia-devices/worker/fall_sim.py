"""Agenda aleatória de quedas mock (suspect → fall → clipe → normal)."""

from __future__ import annotations

import logging
import random
import threading
import time

from worker.clips import upload_clip_from_bus_frames
from worker.frame_bus import FrameBus
from worker.mqtt import MqttBridge

logger = logging.getLogger(__name__)


def next_fall_delay(fall_min_s: float, fall_max_s: float) -> float:
    low = max(1.0, float(fall_min_s))
    high = max(low, float(fall_max_s))
    return random.uniform(low, high)


def run_fall_sequence(
    mqtt: MqttBridge,
    bus: FrameBus,
    *,
    api_base_url: str,
    device_id: str,
    suspect_hold_s: float = 2.0,
) -> None:
    """Uma sequência completa de queda + upload de clipe."""
    mqtt.publish_fall("suspect")
    time.sleep(suspect_hold_s)

    frames = bus.snapshot_clip()
    mqtt.publish_fall("fall")

    upload_clip_from_bus_frames(
        api_base_url,
        device_id,
        frames,
        bus.fps,
    )

    mqtt.publish_fall("normal")


def run_fall_sim_loop(
    mqtt: MqttBridge,
    bus: FrameBus,
    stop_event: threading.Event,
    *,
    api_base_url: str,
    device_id: str,
    fall_min_s: float,
    fall_max_s: float,
) -> None:
    """Loop que dispara quedas em intervalos aleatórios."""
    # primeira thumbnail/stream pode precisar de frames — espera um pouco
    if stop_event.wait(min(5.0, fall_min_s)):
        return

    while not stop_event.is_set():
        delay = next_fall_delay(fall_min_s, fall_max_s)
        logger.info("Próxima queda mock em %.0fs", delay)
        if stop_event.wait(delay):
            break
        try:
            run_fall_sequence(
                mqtt,
                bus,
                api_base_url=api_base_url,
                device_id=device_id,
            )
        except Exception as exc:  # pylint: disable=broad-exception-caught
            logger.warning("Sequência de queda falhou: %s", exc)
            try:
                mqtt.publish_fall("normal")
            except Exception:  # pylint: disable=broad-exception-caught
                pass
