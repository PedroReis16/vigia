"""Lease Redis para claimar um device do pool."""

from __future__ import annotations

import logging
import os
import socket
import threading
import time
from dataclasses import dataclass

import redis

from worker.settings import DEFAULT_RESERVED_EDGE_IDS, DeviceInfo

logger = logging.getLogger(__name__)

KEY_PREFIX = "vigia:mock-device:"


@dataclass(slots=True)
class DeviceClaim:
    device: DeviceInfo
    worker_id: str
    redis_client: redis.Redis
    ttl_s: int
    _stop: threading.Event
    _thread: threading.Thread | None = None

    def start_heartbeat(self) -> None:
        if self._thread is not None:
            return
        self._thread = threading.Thread(
            target=self._heartbeat_loop,
            name="claim-heartbeat",
            daemon=True,
        )
        self._thread.start()

    def release(self) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=2)
            self._thread = None
        key = KEY_PREFIX + self.device.id
        try:
            current = self.redis_client.get(key)
            if current == self.worker_id:
                self.redis_client.delete(key)
                logger.info("Lease libertado: %s", self.device.id)
        except redis.RedisError as exc:
            logger.warning("Falha ao libertar lease %s: %s", self.device.id, exc)

    def _heartbeat_loop(self) -> None:
        interval = max(1.0, self.ttl_s / 3)
        key = KEY_PREFIX + self.device.id
        while not self._stop.wait(interval):
            try:
                current = self.redis_client.get(key)
                if current != self.worker_id:
                    logger.error(
                        "Lease perdido para %s (holder=%s)",
                        self.device.id,
                        current,
                    )
                    self._stop.set()
                    break
                self.redis_client.expire(key, self.ttl_s)
            except redis.RedisError as exc:
                logger.warning("Heartbeat Redis falhou: %s", exc)


def default_worker_id() -> str:
    return f"{socket.gethostname()}:{os.getpid()}"


def _assert_not_reserved(
    device_id: str,
    reserved_ids: frozenset[str] | None = None,
) -> None:
    reserved = reserved_ids or DEFAULT_RESERVED_EDGE_IDS
    if device_id.strip().lower() in reserved:
        raise ValueError(
            f"DEVICE_ID {device_id} é reservado ao edge real e não pode ser "
            "claimado pelo vigia-devices"
        )


def claim_device(
    redis_client: redis.Redis,
    pool: list[DeviceInfo],
    *,
    device_id: str | None = None,
    ttl_s: int = 30,
    worker_id: str | None = None,
    reserved_ids: frozenset[str] | None = None,
) -> DeviceClaim:
    """Claima o primeiro device livre (ou o DEVICE_ID forçado)."""
    if not pool:
        raise ValueError("Pool de devices vazio")

    reserved = reserved_ids or DEFAULT_RESERVED_EDGE_IDS
    for device in pool:
        _assert_not_reserved(device.id, reserved)

    holder = worker_id or default_worker_id()
    stop = threading.Event()

    candidates = pool
    if device_id:
        _assert_not_reserved(device_id, reserved)
        match = next((d for d in pool if d.id == device_id), None)
        if match is None:
            raise ValueError(f"DEVICE_ID {device_id} não está no device_pool.json")
        candidates = [match]

    for device in candidates:
        key = KEY_PREFIX + device.id
        try:
            acquired = redis_client.set(key, holder, nx=True, ex=ttl_s)
        except redis.RedisError as exc:
            raise RuntimeError(f"Redis indisponível para claim: {exc}") from exc

        if acquired:
            logger.info("Device claimado: %s (%s) por %s", device.name, device.id, holder)
            claim = DeviceClaim(
                device=device,
                worker_id=holder,
                redis_client=redis_client,
                ttl_s=ttl_s,
                _stop=stop,
            )
            claim.start_heartbeat()
            return claim

        current = redis_client.get(key)
        if current == holder:
            redis_client.expire(key, ttl_s)
            logger.info("Device já nosso: %s (%s)", device.name, device.id)
            claim = DeviceClaim(
                device=device,
                worker_id=holder,
                redis_client=redis_client,
                ttl_s=ttl_s,
                _stop=stop,
            )
            claim.start_heartbeat()
            return claim

    raise RuntimeError(
        "Nenhum device livre no pool; aumente o pool ou pare outro worker"
    )


def wait_and_claim(
    redis_url: str,
    pool: list[DeviceInfo],
    *,
    device_id: str | None = None,
    ttl_s: int = 30,
    retry_s: float = 2.0,
    stop_event: threading.Event | None = None,
) -> DeviceClaim:
    """Tenta claimar em loop até conseguir ou o stop_event disparar."""
    client = redis.Redis.from_url(redis_url, decode_responses=True)
    while True:
        if stop_event is not None and stop_event.is_set():
            raise RuntimeError("Cancelado antes do claim")
        try:
            return claim_device(
                client,
                pool,
                device_id=device_id,
                ttl_s=ttl_s,
            )
        except RuntimeError as exc:
            message = str(exc)
            if device_id or "Redis indisponível" in message:
                raise
            logger.warning("%s — a tentar de novo em %.1fs", exc, retry_s)
            time.sleep(retry_s)
