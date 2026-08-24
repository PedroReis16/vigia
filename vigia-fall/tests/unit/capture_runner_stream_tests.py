"""Testes do ritmo de captura com streaming desacoplado."""

from unittest.mock import MagicMock, patch

import numpy as np

from capture import capture_runner


def _fake_frame() -> np.ndarray:
    return np.zeros((8, 8, 3), dtype=np.uint8)


def test_run_capture_StreamingOn_MaisWritesShmQueClassificacao() -> None:
    writes = {"n": 0}
    classifies = {"n": 0}
    reads = {"n": 0}

    mock_cap = MagicMock()
    mock_cap.isOpened.return_value = True
    mock_cap.get.return_value = 30.0

    def _read():
        reads["n"] += 1
        if reads["n"] > 5:
            return False, None
        return True, _fake_frame()

    mock_cap.read.side_effect = _read

    mock_shm = MagicMock()
    mock_shm.write.side_effect = lambda _frame, _fps: writes.__setitem__("n", writes["n"] + 1) or True

    mock_worker = MagicMock()
    mock_worker.run.return_value = None

    times = iter([0.0, 0.0, 0.05, 0.05, 0.10, 0.10, 0.20, 0.20, 0.30, 0.30])

    fake_cv2 = MagicMock()
    fake_cv2.VideoCapture.return_value = mock_cap
    fake_cv2.flip.side_effect = lambda frame, _code: frame

    with (
        patch.object(capture_runner, "get_settings") as mock_settings,
        patch.object(capture_runner, "cv2", fake_cv2),
        patch.object(capture_runner, "_resolve_stream_fps", return_value=30),
        patch.object(capture_runner, "FrameShmRing") as mock_shm_cls,
        patch.object(capture_runner, "get_worker", return_value=mock_worker),
        patch.object(capture_runner, "get_stream_status", return_value=True),
        patch.object(capture_runner, "maybe_upload_thumbnail"),
        patch.object(capture_runner.time, "monotonic", side_effect=lambda: next(times, 1.0)),
        patch.object(capture_runner, "ThreadPoolExecutor") as mock_executor_cls,
    ):
        mock_settings.return_value.capture_source = 0
        mock_settings.return_value.show_video = False
        mock_settings.return_value.capture_loop = False
        mock_settings.return_value.frame_rate = 10
        mock_shm_cls.attach.return_value = mock_shm

        executor = MagicMock()
        mock_executor_cls.return_value = executor

        def _track_classify(frame, now):
            classifies["n"] += 1

        mock_worker.insert_raw_frame.side_effect = _track_classify

        try:
            capture_runner.run_capture(frame_shm_name="shm-test")
        except StopIteration:
            pass

    assert writes["n"] > classifies["n"]
    assert classifies["n"] >= 1


def test_resolve_stream_fps_FallbackQuandoZero() -> None:
    cap = MagicMock()
    cap.get.return_value = 0.0
    assert capture_runner._resolve_stream_fps(cap) == 30


def test_resolve_stream_fps_LimitaValorAbsurdo() -> None:
    cap = MagicMock()
    cap.get.return_value = 240.0
    assert capture_runner._resolve_stream_fps(cap) == 30
