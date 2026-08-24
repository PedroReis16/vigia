"""Testes de normalização e publicação de fall_state."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from integration.fiware_runner import normalize_fall_state, notify_fall


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


def test_notify_fall_publica_valor_canonico() -> None:
    mock_client = MagicMock()
    with (
        patch("integration.fiware_runner.get_device_identity") as identity,
        patch("integration.fiware_runner.get_network_settings") as network,
        patch("integration.fiware_runner.mqtt.Client", return_value=mock_client),
    ):
        identity.return_value = MagicMock(device_id="dev-1")
        network.return_value = MagicMock(
            api_base_url="https://services.example.com",
            fiware_api_key="apikey",
        )

        notify_fall("FALL")

        mock_client.publish.assert_called_once_with(
            "/apikey/dev-1/attrs",
            "fall|fall",
        )
        mock_client.disconnect.assert_called_once()
