"""Testes unitários para o runner do processo de streaming."""

from multiprocessing import Event
from unittest.mock import MagicMock, patch

import numpy as np

from streaming import stream_runner
from streaming.frame_shm import FrameRead, FrameShmRing


def test_run_stream_EventLimpo_EncerraEChamaShutdown() -> None:
    stream_event = Event()

    mock_shm = MagicMock(spec=FrameShmRing)
    with (
        patch.object(stream_runner, "FrameShmRing") as mock_cls,
        patch.object(stream_runner, "publish_frame") as mock_publish,
        patch.object(stream_runner, "shutdown_stream") as mock_shutdown,
    ):
        mock_cls.attach.return_value = mock_shm
        stream_runner.run_stream("shm-test", stream_event)

    mock_publish.assert_not_called()
    mock_shutdown.assert_called_once()
    mock_shm.close.assert_called_once()


def test_run_stream_ComFrame_ChamaPublishFrameESaiQuandoEventClear() -> None:
    stream_event = Event()
    stream_event.set()

    frame = np.zeros((4, 4, 3), dtype=np.uint8)
    mock_shm = MagicMock(spec=FrameShmRing)
    mock_shm.read_latest.side_effect = [
        FrameRead(frame=frame, stream_fps=30),
        None,
    ]

    call_count = {"n": 0}

    def _publish_then_clear(_frame: np.ndarray, _fps: int) -> None:
        call_count["n"] += 1
        stream_event.clear()

    with (
        patch.object(stream_runner, "FrameShmRing") as mock_cls,
        patch.object(stream_runner, "publish_frame", side_effect=_publish_then_clear),
        patch.object(stream_runner, "shutdown_stream") as mock_shutdown,
    ):
        mock_cls.attach.return_value = mock_shm
        stream_runner.run_stream("shm-test", stream_event)

    assert call_count["n"] == 1
    mock_shutdown.assert_called_once()


def test_run_stream_SemFrameNovo_ContinuaAteEventClear() -> None:
    stream_event = Event()
    stream_event.set()

    polls = {"n": 0}

    def _fake_read(timeout=0.2):
        polls["n"] += 1
        if polls["n"] >= 2:
            stream_event.clear()
        return None

    mock_shm = MagicMock(spec=FrameShmRing)
    mock_shm.read_latest.side_effect = _fake_read

    with (
        patch.object(stream_runner, "FrameShmRing") as mock_cls,
        patch.object(stream_runner, "publish_frame") as mock_publish,
        patch.object(stream_runner, "shutdown_stream") as mock_shutdown,
    ):
        mock_cls.attach.return_value = mock_shm
        stream_runner.run_stream("shm-test", stream_event)

    assert polls["n"] >= 2
    mock_publish.assert_not_called()
    mock_shutdown.assert_called_once()
