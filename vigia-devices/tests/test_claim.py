from __future__ import annotations

from typing import Any

import pytest

from worker.claim import KEY_PREFIX, claim_device
from worker.settings import DeviceInfo


class FakeRedis:
    def __init__(self) -> None:
        self.store: dict[str, str] = {}
        self.ttls: dict[str, int] = {}

    def set(self, key: str, value: str, nx: bool = False, ex: int | None = None) -> bool:
        if nx and key in self.store:
            return False
        self.store[key] = value
        if ex is not None:
            self.ttls[key] = ex
        return True

    def get(self, key: str) -> str | None:
        return self.store.get(key)

    def expire(self, key: str, ttl: int) -> bool:
        if key not in self.store:
            return False
        self.ttls[key] = ttl
        return True

    def delete(self, key: str) -> int:
        return 1 if self.store.pop(key, None) is not None else 0


def _pool() -> list[DeviceInfo]:
    return [
        DeviceInfo("id-1", "Vigia-aaaa1111", "A", "AA:01", "LivingRoom"),
        DeviceInfo("id-2", "Vigia-bbbb2222", "B", "AA:02", "Bedroom"),
    ]


def test_claim_takes_first_free_device():
    client: Any = FakeRedis()
    claim = claim_device(client, _pool(), worker_id="w1", ttl_s=30)
    try:
        assert claim.device.id == "id-1"
        assert client.get(KEY_PREFIX + "id-1") == "w1"
    finally:
        claim.release()
    assert client.get(KEY_PREFIX + "id-1") is None


def test_claim_skips_busy_and_takes_next():
    client: Any = FakeRedis()
    first = claim_device(client, _pool(), worker_id="w1", ttl_s=30)
    second = claim_device(client, _pool(), worker_id="w2", ttl_s=30)
    try:
        assert first.device.id == "id-1"
        assert second.device.id == "id-2"
    finally:
        first.release()
        second.release()


def test_claim_forced_device_id():
    client: Any = FakeRedis()
    claim = claim_device(
        client,
        _pool(),
        device_id="id-2",
        worker_id="w1",
        ttl_s=30,
    )
    try:
        assert claim.device.id == "id-2"
    finally:
        claim.release()


def test_claim_raises_when_pool_exhausted():
    client: Any = FakeRedis()
    a = claim_device(client, _pool(), worker_id="w1", ttl_s=30)
    b = claim_device(client, _pool(), worker_id="w2", ttl_s=30)
    try:
        with pytest.raises(RuntimeError, match="Nenhum device livre"):
            claim_device(client, _pool(), worker_id="w3", ttl_s=30)
    finally:
        a.release()
        b.release()


def test_claim_rejects_reserved_edge_device_id():
    client: Any = FakeRedis()
    reserved = frozenset({"b7e3c9a1-4f2d-4e8b-9c1a-6d5e4f3a2b1c"})
    with pytest.raises(ValueError, match="reservado ao edge real"):
        claim_device(
            client,
            _pool(),
            device_id="b7e3c9a1-4f2d-4e8b-9c1a-6d5e4f3a2b1c",
            worker_id="w1",
            ttl_s=30,
            reserved_ids=reserved,
        )


def test_claim_rejects_pool_entry_in_reserved_set():
    client: Any = FakeRedis()
    reserved = frozenset({"id-1"})
    with pytest.raises(ValueError, match="reservado ao edge real"):
        claim_device(client, _pool(), worker_id="w1", ttl_s=30, reserved_ids=reserved)
