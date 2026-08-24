"""Testes de normalização e publicação de fall_state via loop FIWARE."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from integration.fiware_runner import apply_fall_label, normalize_fall_state


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("FALL", "fall"),
        ("fall", "fall"),
        ("NORMAL", "normal"),
        ("ADL", "normal"),
        ("SUSPECT", "suspect"),
        ("FALSE_POSITIVE", "false_positive"),
    ],
)
def test_normalize_fall_state(raw: str, expected: str) -> None:
    assert normalize_fall_state(raw) == expected


def test_apply_fall_label_publica_valor_canonico() -> None:
    client = MagicMock()
    last = apply_fall_label(client, "/apikey/dev-1/attrs", "FALL", None)

    assert last == "fall"
    client.publish.assert_called_once_with("/apikey/dev-1/attrs", "fall|fall")


def test_apply_fall_label_dedupe_nao_republica() -> None:
    client = MagicMock()
    last = apply_fall_label(client, "/topic", "NORMAL", None)
    last = apply_fall_label(client, "/topic", "NORMAL", last)
    last = apply_fall_label(client, "/topic", "ADL", last)

    assert last == "normal"
    client.publish.assert_called_once_with("/topic", "fall|normal")
