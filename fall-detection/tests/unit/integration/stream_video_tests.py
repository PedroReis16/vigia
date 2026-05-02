"""Testes unitários para streaming de frames brutos via FFmpeg."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import numpy as np
import pytest

import app.streaming.stream_video as stream_video_module


@pytest.fixture(autouse=True)
def reset_stream_video_globals() -> None:
    stream_video_module._process = None
    stream_video_module._frame_size = None
    yield
    stream_video_module._process = None
    stream_video_module._frame_size = None


def test_stream_video_given_first_frame_should_spawn_ffmpeg_with_matching_geometry() -> None:
    fake_stdin = MagicMock()
    proc = MagicMock()
    proc.stdin = fake_stdin
    frame = np.zeros((240, 320, 3), dtype=np.uint8)
    rtmp = "rtmp://localhost/live/stream_key"

    with patch(
        "app.streaming.stream_video.subprocess.Popen",
        return_value=proc,
    ) as popen_mock:
        stream_video_module.stream_video(frame, rtmp)

    popen_mock.assert_called_once()
    cmd = popen_mock.call_args[0][0]
    assert "ffmpeg" in cmd[0]
    assert "-s" in cmd
    assert "320x240" in cmd
    assert cmd[-1] == rtmp
    fake_stdin.write.assert_called_once()


def test_stream_video_given_second_frame_should_reuse_single_ffmpeg_process() -> None:
    fake_stdin = MagicMock()
    proc = MagicMock()
    proc.stdin = fake_stdin

    with patch("app.streaming.stream_video.subprocess.Popen", return_value=proc) as popen_mock:
        stream_video_module.stream_video(np.zeros((10, 20, 3), dtype=np.uint8), "rtmp://x/y")
        stream_video_module.stream_video(np.zeros((10, 20, 3), dtype=np.uint8), "rtmp://x/y")

    assert popen_mock.call_count == 1
    assert fake_stdin.write.call_count == 2


def test_stream_video_given_stdin_closed_should_raise_runtime_error() -> None:
    proc = MagicMock()
    proc.stdin = None

    with (
        patch("app.streaming.stream_video.subprocess.Popen", return_value=proc),
        pytest.raises(RuntimeError, match="stdin"),
    ):
        stream_video_module.stream_video(np.zeros((4, 4, 3), dtype=np.uint8), "rtmp://z")
