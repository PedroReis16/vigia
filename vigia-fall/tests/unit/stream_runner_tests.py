"""Testes unitários para o runner do processo de streaming."""

from multiprocessing import Event, Queue
from unittest.mock import patch

import numpy as np

from streaming import stream_runner
from streaming.frame_ipc import put_frame


def test_run_stream_EventLimpo_EncerraEChamaShutdown() -> None:
    frame_queue: Queue = Queue(maxsize=2)
    stream_event = Event()
    # Event não setado → loop não entra / sai imediatamente

    with (
        patch.object(stream_runner, "stream_video") as mock_stream,
        patch.object(stream_runner, "shutdown_stream") as mock_shutdown,
    ):
        stream_runner.run_stream(frame_queue, stream_event)

    mock_stream.assert_not_called()
    mock_shutdown.assert_called_once()


def test_run_stream_ComFrame_ChamaStreamVideoESaiQuandoEventClear() -> None:
    frame_queue: Queue = Queue(maxsize=2)
    stream_event = Event()
    stream_event.set()

    frame = np.zeros((4, 4, 3), dtype=np.uint8)
    put_frame(frame_queue, frame)

    call_count = {"n": 0}

    def _stream_then_clear(_frame: np.ndarray) -> None:
        call_count["n"] += 1
        stream_event.clear()

    with (
        patch.object(stream_runner, "stream_video", side_effect=_stream_then_clear),
        patch.object(stream_runner, "shutdown_stream") as mock_shutdown,
    ):
        stream_runner.run_stream(frame_queue, stream_event)

    assert call_count["n"] == 1
    mock_shutdown.assert_called_once()


def test_run_stream_TimeoutSemFrame_ContinuaAteEventClear() -> None:
    frame_queue: Queue = Queue(maxsize=2)
    stream_event = Event()
    stream_event.set()

    polls = {"n": 0}

    def _fake_get(_queue, timeout=0.2):
        polls["n"] += 1
        if polls["n"] >= 2:
            stream_event.clear()
        return None

    with (
        patch.object(stream_runner, "get_frame", side_effect=_fake_get),
        patch.object(stream_runner, "stream_video") as mock_stream,
        patch.object(stream_runner, "shutdown_stream") as mock_shutdown,
    ):
        stream_runner.run_stream(frame_queue, stream_event)

    assert polls["n"] >= 2
    mock_stream.assert_not_called()
    mock_shutdown.assert_called_once()
