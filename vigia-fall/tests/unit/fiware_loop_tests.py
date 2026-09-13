"""Testes do loop de publicação fall_state no processo FIWARE."""

from __future__ import annotations

from unittest.mock import MagicMock

from integration.fiware_runner import _publish_fall_state, normalize_fall_state
from shared.event_shm import EventShmRing
from shared.event_types import EVENT_FALL_STATE


def _drain_shm_labels(client: MagicMock, topic: str, labels: list[str]) -> str | None:
    """Simula o poll da fall SHM publicando cada evento enfileirado."""
    ring = EventShmRing.create(slot_count=8, payload_max=64)
    try:
        for label in labels:
            ring.write(EVENT_FALL_STATE, label)
        last: str | None = None
        while True:
            event = ring.read_next(timeout=0.05)
            if event is None:
                break
            state = normalize_fall_state(event.payload)
            _publish_fall_state(client, topic, state)
            last = state
        return last
    finally:
        ring.close()
        ring.unlink()


def test_fiware_loop_publica_cada_evento_da_shm() -> None:
    client = MagicMock()
    last = _drain_shm_labels(
        client,
        "/key/dev/attrs",
        ["NORMAL", "NORMAL", "SUSPECT", "SUSPECT", "FALL", "FALL"],
    )

    assert last == "fall"
    assert client.publish.call_args_list == [
        (("/key/dev/attrs", "fall|normal"),),
        (("/key/dev/attrs", "fall|normal"),),
        (("/key/dev/attrs", "fall|suspect"),),
        (("/key/dev/attrs", "fall|suspect"),),
        (("/key/dev/attrs", "fall|fall"),),
        (("/key/dev/attrs", "fall|fall"),),
    ]


def test_fiware_loop_normaliza_aliases_por_evento() -> None:
    client = MagicMock()
    last = _drain_shm_labels(client, "/t", ["NORMAL", "ADL", "ok"])

    assert last == "normal"
    assert client.publish.call_args_list == [
        (("/t", "fall|normal"),),
        (("/t", "fall|normal"),),
        (("/t", "fall|normal"),),
    ]
