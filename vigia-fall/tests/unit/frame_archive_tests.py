"""Testes do CaptureFrameArchive."""

import numpy as np
import pytest

from capture.frame_archive import CaptureFrameArchive


def _frame(value: int) -> np.ndarray:
    return np.full((4, 4, 3), value, dtype=np.uint8)


def test_frame_archive_RetémMaxFrames() -> None:
    archive = CaptureFrameArchive(max_frames=3)

    archive.push(_frame(1), 1.0)
    archive.push(_frame(2), 2.0)
    archive.push(_frame(3), 3.0)
    archive.push(_frame(4), 4.0)

    assert len(archive) == 3
    snapshot = archive.snapshot()
    assert len(snapshot) == 3
    assert snapshot[0][1] == 2.0
    assert snapshot[-1][0][0, 0, 0] == 4


def test_frame_archive_SnapshotCopiaIndependente() -> None:
    archive = CaptureFrameArchive(max_frames=2)
    frame = _frame(7)
    archive.push(frame, 1.0)

    snapshot = archive.snapshot()
    snapshot[0][0][0, 0, 0] = 99

    assert archive.snapshot()[0][0][0, 0, 0] == 7


def test_frame_archive_PushSemCopy_ReutilizaReferencia() -> None:
    archive = CaptureFrameArchive(max_frames=2)
    frame = _frame(5)
    archive.push(frame, 1.0, copy=False)
    frame[0, 0, 0] = 99

    assert archive.snapshot()[0][0][0, 0, 0] == 99


def test_frame_archive_RejeitaMaxFramesInvalido() -> None:
    with pytest.raises(ValueError, match="max_frames"):
        CaptureFrameArchive(max_frames=0)
