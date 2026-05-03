"""Testes unitários para o classificador de ações (app.core.action_classifier)."""

from __future__ import annotations

import queue
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from app.core.action_classifier import run_classifier


class _StopClassifierLoop(Exception):
    """Só para encerrar o ``while True`` nos testes sem KeyboardInterrupt."""


def test_run_classifier_given_window_should_process_until_stop() -> None:
    buffer = MagicMock()
    window = np.zeros((30, 51), dtype=np.float32)
    buffer.get.side_effect = [(42, window), _StopClassifierLoop()]

    with (
        patch("app.core.action_classifier._send_notification") as notify,
        pytest.raises(_StopClassifierLoop),
    ):
        run_classifier(buffer)

    buffer.get.assert_called()
    notify.assert_called_once()


def test_run_classifier_given_empty_queue_should_retry_until_stop() -> None:
    buffer = MagicMock()
    buffer.get.side_effect = [queue.Empty(), queue.Empty(), _StopClassifierLoop()]

    with (
        patch("app.core.action_classifier._send_notification") as notify,
        pytest.raises(_StopClassifierLoop),
    ):
        run_classifier(buffer)

    assert buffer.get.call_count >= 2
    notify.assert_not_called()
