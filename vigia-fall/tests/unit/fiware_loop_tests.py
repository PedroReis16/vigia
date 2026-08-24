"""Testes do loop de publicação fall_state no processo FIWARE."""

from __future__ import annotations

from queue import Empty, Queue
from unittest.mock import MagicMock

from integration.fiware_runner import apply_fall_label


def _drain_labels(client: MagicMock, topic: str, labels: list[str]) -> str | None:
    """Simula o poll da fall_queue aplicando cada label com dedupe."""
    last: str | None = None
    q: Queue = Queue()
    for label in labels:
        q.put(label)
    while True:
        try:
            label = q.get_nowait()
        except Empty:
            break
        last = apply_fall_label(client, topic, label, last)
    return last


def test_fiware_loop_publica_so_em_transicao() -> None:
    client = MagicMock()
    last = _drain_labels(
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
    last = _drain_labels(client, "/t", ["NORMAL", "ADL", "ok"])

    assert last == "normal"
    client.publish.assert_called_once_with("/t", "fall|normal")
