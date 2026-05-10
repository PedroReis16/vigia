"""Testes unitários para streaming de frames brutos via FFmpeg."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import numpy as np
import pytest

import app.streaming.stream_video as stream_video_module


@pytest.fixture(autouse=True)
def patch_ffmpeg_which() -> None:
    """CI/dev sem ffmpeg no PATH: resolve para um caminho fixo."""
    with patch(
        "app.streaming.stream_video.shutil.which",
        return_value="/usr/bin/ffmpeg",
    ):
        yield


@pytest.fixture(autouse=True)
def reset_stream_video_globals() -> None:
    state = stream_video_module._rtmp_stream_state
    state.process = None
    state.frame_size = None
    yield
    state.process = None
    state.frame_size = None


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
    assert cmd[0].endswith("ffmpeg")
    assert "-s" in cmd
    assert "320x240" in cmd
    assert cmd[-1] == rtmp
    assert "env" in popen_mock.call_args.kwargs
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


def test_ffmpeg_subprocess_env_should_strip_pyinstaller_ld_path(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(
        "LD_LIBRARY_PATH",
        "/opt/vigia/fall-detection/_internal:/usr/lib/aarch64-linux-gnu",
    )
    monkeypatch.setattr(stream_video_module.sys, "_MEIPASS", "/tmp/_MEIxyz", raising=False)
    env = stream_video_module._ffmpeg_subprocess_env()
    assert "_internal" not in env.get("LD_LIBRARY_PATH", "")
    assert "aarch64-linux-gnu" in env["LD_LIBRARY_PATH"]


def test_stream_video_given_ffmpeg_missing_from_path_should_raise_runtime_error() -> None:
    with (
        patch("app.streaming.stream_video.shutil.which", return_value=None),
        pytest.raises(RuntimeError, match="ffmpeg nao encontrado"),
    ):
        stream_video_module.stream_video(
            np.zeros((4, 4, 3), dtype=np.uint8), "rtmp://z"
        )


def test_stream_video_given_stdin_closed_should_raise_runtime_error() -> None:
    proc = MagicMock()
    proc.stdin = None

    with (
        patch("app.streaming.stream_video.subprocess.Popen", return_value=proc),
        pytest.raises(RuntimeError, match="stdin"),
    ):
        stream_video_module.stream_video(np.zeros((4, 4, 3), dtype=np.uint8), "rtmp://z")
