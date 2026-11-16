"""Testes do publisher RTMP (sem FFmpeg real)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from stream import rtmp as rtmp_mod


@pytest.fixture(autouse=True)
def _reset_rtmp():
    rtmp_mod.reset_rtmp_for_tests()
    yield
    rtmp_mod.reset_rtmp_for_tests()


def test_rtmp_publish_url() -> None:
    assert (
        rtmp_mod._rtmp_publish_url("rtmp://host:1935", "dev1")
        == "rtmp://host:1935/live/dev1"
    )
    with pytest.raises(ValueError):
        rtmp_mod._rtmp_publish_url("http://host", "dev1")


def test_publish_frame_ChamaPublisher() -> None:
    frame = np.zeros((4, 4, 3), dtype=np.uint8)
    publisher = MagicMock()
    publisher.is_running = False

    with (
        patch.object(rtmp_mod, "_publisher", publisher),
        patch.object(
            rtmp_mod,
            "_resolve_target",
            return_value=(12, "rtmp://x/live/d"),
        ),
    ):
        rtmp_mod.publish_frame(frame, 12)

    publisher.start.assert_called_once()
    publisher.write.assert_called_once()


def test_publish_frame_MaxFalhas_DesligaStream() -> None:
    frame = np.zeros((4, 4, 3), dtype=np.uint8)

    with (
        patch.object(
            rtmp_mod,
            "_resolve_target",
            side_effect=RuntimeError("down"),
        ),
        patch.object(rtmp_mod, "set_stream_status") as set_status,
        patch.object(rtmp_mod, "_publisher") as publisher,
    ):
        publisher.stop = MagicMock()
        for _ in range(rtmp_mod._MAX_RECONNECT_ATTEMPTS):
            rtmp_mod._next_attempt_at = 0.0
            rtmp_mod.publish_frame(frame, 12)

        set_status.assert_called_with(False)
