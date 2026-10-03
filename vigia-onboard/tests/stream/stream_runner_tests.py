"""Testes dos runners de stream/clips e supervisor."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import numpy as np
import pytest

import stream as stream_pkg
from shared.live_frame_shm import LiveFrameShm
from stream import clips_runner, stream_runner
from stream.rtmp import reset_rtmp_for_tests


@pytest.fixture(autouse=True)
def _reset_workers():
    stream_pkg.stop_all_workers(join_timeout=0.5)
    reset_rtmp_for_tests()
    yield
    stream_pkg.stop_all_workers(join_timeout=0.5)
    reset_rtmp_for_tests()


def test_stream_runner_PublicaEnquantoStreamOn() -> None:
    live = LiveFrameShm.create(max_payload=64)
    frame = np.zeros((2, 2, 3), dtype=np.uint8)
    live.write(frame, 12)

    calls = {"n": 0}

    def on_then_off():
        calls["n"] += 1
        return calls["n"] <= 1

    try:
        with (
            patch.object(stream_runner, "get_stream_on", side_effect=on_then_off),
            patch.object(stream_runner, "publish_frame") as publish,
            patch.object(stream_runner, "shutdown_stream") as shutdown,
        ):
            stream_runner.run_stream_worker(live.name)

        publish.assert_called_once()
        np.testing.assert_array_equal(publish.call_args[0][0], frame)
        assert publish.call_args[0][1] == 12
        shutdown.assert_called_once()
    finally:
        live.close()
        live.unlink()


def test_clips_runner_EmpilhaNaJanela() -> None:
    live = LiveFrameShm.create(max_payload=64)
    frame = np.full((2, 2, 3), 7, dtype=np.uint8)
    live.write(frame, 12)

    clip = MagicMock()
    calls = {"n": 0}

    def on_then_off():
        calls["n"] += 1
        return calls["n"] <= 1

    try:
        with (
            patch.object(clips_runner, "get_clips_enabled", side_effect=on_then_off),
            patch.object(clips_runner, "get_settings") as settings,
            patch.object(
                clips_runner.ClipFrameRing,
                "open_or_create",
                return_value=clip,
            ),
        ):
            settings.return_value = MagicMock(
                clip_shm_name="clip-test",
                clip_slot_count=4,
                clip_max_payload=64,
            )
            clips_runner.run_clips_worker(live.name, "clip-test")

        clip.push.assert_called_once()
        np.testing.assert_array_equal(clip.push.call_args[0][0], frame)
        clip.close.assert_called_once()
    finally:
        live.close()
        live.unlink()


def test_supervise_workers_SobeEParaIndependentes() -> None:
    live = MagicMock()
    live.name = "live"

    with (
        patch.object(stream_pkg, "ensure_stream_worker") as ensure_stream,
        patch.object(stream_pkg, "ensure_clips_worker") as ensure_clips,
        patch.object(stream_pkg, "stop_stream_worker") as stop_stream,
        patch.object(stream_pkg, "stop_clips_worker") as stop_clips,
    ):
        stream_pkg._stream_task = None
        stream_pkg._clips_task = None

        stream_pkg.supervise_workers(
            "live",
            stream_on=True,
            clips_enabled=False,
            live_shm=live,
        )
        ensure_stream.assert_called_once_with("live")
        ensure_clips.assert_not_called()

        fake_stream = MagicMock()
        fake_stream.is_alive.return_value = True
        stream_pkg._stream_task = fake_stream

        stream_pkg.supervise_workers(
            "live",
            stream_on=False,
            clips_enabled=True,
            clip_shm_name="clip",
            live_shm=live,
        )
        stop_stream.assert_called_once()
        ensure_clips.assert_called_once_with("live", "clip")
        stop_clips.assert_not_called()
