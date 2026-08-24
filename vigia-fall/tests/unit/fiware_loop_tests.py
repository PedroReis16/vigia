"""Testes do loop de publicação fall_state no processo FIWARE."""

from __future__ import annotations

from unittest.mock import MagicMock

from integration.fiware_runner import apply_fall_label
from shared.event_shm import EventShmRing
from shared.event_types import EVENT_FALL_STATE


def _drain_shm_labels(client: MagicMock, topic: str, labels: list[str]) -> str | None:
    """Simula o poll da fall SHM aplicando cada label com dedupe."""
    ring = EventShmRing.create(slot_count=8, payload_max=64)
    try:
        for label in labels:
            ring.write(EVENT_FALL_STATE, label)
        last: str | None = None
        while True:
            event = ring.read_next(timeout=0.05)
            if event is None:
                break
            last = apply_fall_label(client, topic, event.payload, last)
        return last
    finally:
        ring.close()
        ring.unlink()


def test_fiware_loop_publica_so_em_transicao() -> None:
    client = MagicMock()
    last = _drain_shm_labels(
        client,
        "/key/dev/attrs",
        ["NORMAL", "NORMAL", "SUSPECT", "SUSPECT", "FALL", "FALL"],
    )

    assert last == "fall"
    assert client.publish.call_args_list == [
        (("/key/dev/attrs", "fall|normal"),),
        (("/key/dev/attrs", "fall|suspect"),),
        (("/key/dev/attrs", "fall|fall"),),
    ]


def test_fiware_loop_aliases_contam_como_mesmo_estado() -> None:
    client = MagicMock()
    last = _drain_shm_labels(client, "/t", ["NORMAL", "ADL", "ok"])

    assert last == "normal"
    client.publish.assert_called_once_with("/t", "fall|normal")
