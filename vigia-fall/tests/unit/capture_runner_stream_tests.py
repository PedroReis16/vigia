"""Testes do ritmo de captura full-rate com classificação subsampled."""

from unittest.mock import MagicMock, patch

import numpy as np

from capture import capture_runner
from capture.frame_archive import CaptureFrameArchive


def _fake_frame() -> np.ndarray:
    return np.zeros((8, 8, 3), dtype=np.uint8)


def _run_capture_with_mocks(
    *,
    stream_on: bool,
    frame_rate: int = 10,
    max_reads: int = 5,
) -> tuple[int, int, int]:
    """Retorna (reads, classifies, shm_writes)."""
    reads = {"n": 0}
    classifies = {"n": 0}
    writes = {"n": 0}

    mock_cap = MagicMock()
    mock_cap.isOpened.return_value = True
    mock_cap.get.return_value = 30.0

    def _read():
        if reads["n"] >= max_reads:
            return False, None
        reads["n"] += 1
        return True, _fake_frame()

    mock_cap.read.side_effect = _read

    mock_shm = MagicMock()
    mock_shm.write.side_effect = (
        lambda _frame, _fps: writes.__setitem__("n", writes["n"] + 1) or True
    )

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
        patch.object(
            capture_runner,
            "get_stream_status",
            return_value=stream_on,
        ),
        patch.object(capture_runner, "maybe_upload_thumbnail"),
        patch.object(
            capture_runner.time,
            "monotonic",
            side_effect=lambda: next(times, 1.0),
        ),
        patch.object(capture_runner, "ThreadPoolExecutor") as mock_executor_cls,
        patch.object(
            capture_runner,
            "CaptureFrameArchive",
            side_effect=lambda max_frames: CaptureFrameArchive(max_frames=max_frames),
        ),
    ):
        mock_settings.return_value.capture_source = 0
        mock_settings.return_value.show_video = False
        mock_settings.return_value.capture_loop = False
        mock_settings.return_value.frame_rate = frame_rate
        mock_settings.return_value.capture_archive_frames = 300
        mock_shm_cls.attach.return_value = mock_shm

        executor = MagicMock()
        mock_executor_cls.return_value = executor

        def _track_classify(frame, now):
            classifies["n"] += 1

        mock_worker.insert_raw_frame.side_effect = _track_classify

        try:
            capture_runner.run_capture(
                frame_shm_name="shm-test" if stream_on else None,
            )
        except StopIteration:
            pass

    return reads["n"], classifies["n"], writes["n"]


def test_run_capture_SempreLeTodosOsFrames() -> None:
    reads, classifies, writes = _run_capture_with_mocks(stream_on=False)

    assert reads > classifies
    assert classifies >= 1
    assert writes == 0


def test_run_capture_StreamingOn_LeTodosEClassificaSubsampled() -> None:
    reads, classifies, writes = _run_capture_with_mocks(stream_on=True)

    assert reads == writes
    assert classifies < reads
    assert classifies >= 1


def test_resolve_stream_fps_FallbackQuandoZero() -> None:
    cap = MagicMock()
    cap.get.return_value = 0.0
    assert capture_runner._resolve_stream_fps(cap) == 30


def test_resolve_stream_fps_LimitaValorAbsurdo() -> None:
    cap = MagicMock()
    cap.get.return_value = 240.0
    assert capture_runner._resolve_stream_fps(cap) == 30
