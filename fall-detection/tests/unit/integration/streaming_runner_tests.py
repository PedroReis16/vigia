"""Testes unitários para o runner de streaming (ZMQ → RTMP)."""

from __future__ import annotations

import pickle
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from app.config import Settings
from app.streaming.runner import _consume_frames, run_streaming


def test_consume_frames_given_multipart_frame_should_call_stream_video(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    arr = np.zeros((8, 8, 3), dtype=np.uint8)
    payload = pickle.dumps(arr)
    stream_mock = MagicMock()

    mock_socket = MagicMock()
    mock_socket.recv_multipart.side_effect = [
        [b"frame", payload],
        KeyboardInterrupt(),
    ]

    mock_context = MagicMock()
    mock_context.socket.return_value = mock_socket

    monkeypatch.setattr(
        "app.streaming.runner.zmq.Context",
        lambda *args: mock_context,
    )

    with patch("app.streaming.runner.stream_video", stream_mock):
        _consume_frames("rtmp://unit/test")

    stream_mock.assert_called_once()
    called_frame, url = stream_mock.call_args[0]
    assert np.array_equal(called_frame, arr)
    assert url == "rtmp://unit/test"

    mock_socket.close.assert_called_once()
    mock_context.term.assert_called_once()


def test_consume_frames_given_stream_video_error_should_log_and_reraise(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    mock_socket = MagicMock()
    mock_socket.recv_multipart.side_effect = [[b"frame", pickle.dumps(np.zeros((2, 2, 3)))]]

    mock_context = MagicMock()
    mock_context.socket.return_value = mock_socket

    monkeypatch.setattr(
        "app.streaming.runner.zmq.Context",
        lambda *args: mock_context,
    )

    logged: list[str] = []

    def fake_error(msg: str, *args: object) -> None:
        logged.append(msg)

    monkeypatch.setattr("app.streaming.runner.logger.error", fake_error)

    with (
        patch(
            "app.streaming.runner.stream_video",
            side_effect=RuntimeError("boom"),
        ),
        pytest.raises(RuntimeError, match="boom"),
    ):
        _consume_frames("rtmp://unit/err")

    assert logged and "transmitir" in logged[0].lower()


def test_run_streaming_given_process_exits_should_stop_cleanly(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Loop principal detecta filho morto e encerra (sem subprocess real)."""

    device_id = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"

    class DummyProcess:
        def __init__(self, *_a: object, **_k: object) -> None:
            self.pid = 4242

        def start(self) -> None:
            return None

        def is_alive(self) -> bool:
            return False

        def terminate(self) -> None:
            return None

        def join(self, timeout: float | None = None) -> None:
            return None

    monkeypatch.setattr(
        "app.streaming.runner.load_local_device_settings_required",
        lambda: MagicMock(device_id=device_id),
    )
    monkeypatch.setattr("app.streaming.runner.Process", DummyProcess)

    logged_info: list[str] = []

    monkeypatch.setattr(
        "app.streaming.runner.logger.info",
        lambda msg, *a: logged_info.append(str(msg)),
    )

    settings = Settings(
        data_path="data",
        stream_ingest_url="rtmp://host/live",
        captures_per_second=0,
        video_capture_source=0,
        show_video=False,
        yolo_pose_model=None,
        pose_csv_window_seconds=3.0,
        integration_interval_seconds=60,
    )

    run_streaming(settings)

    assert any("finalizado" in m.lower() for m in logged_info)
