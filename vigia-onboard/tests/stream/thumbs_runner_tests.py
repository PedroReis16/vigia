"""Testes do processo de thumbnails."""

from __future__ import annotations

from unittest.mock import patch

import numpy as np

from shared.live_frame_shm import LiveFrameShm
from stream import thumbs_runner


class _Run:
    def __init__(self) -> None:
        self._on = True

    def is_set(self) -> bool:
        return self._on

    def clear(self) -> None:
        self._on = False


def test_thumbs_worker_EnviaOFrameMaisRecente() -> None:
    live = LiveFrameShm.create(max_payload=64)
    frame = np.full((2, 2, 3), 9, dtype=np.uint8)
    live.write(frame, 12)
    run = _Run()
    sent: list[np.ndarray] = []

    def _upload(image: np.ndarray) -> bool:
        sent.append(image.copy())
        run.clear()
        return True

    try:
        with patch.object(thumbs_runner, "upload_thumbnail", side_effect=_upload):
            thumbs_runner.run_thumbs_worker(live.name, run)  # type: ignore[arg-type]

        assert len(sent) == 1
        np.testing.assert_array_equal(sent[0], frame)
    finally:
        live.close()
        live.unlink()


def test_thumbs_worker_FalhaEsperaAntesDeRepetir() -> None:
    live = LiveFrameShm.create(max_payload=64)
    live.write(np.zeros((2, 2, 3), dtype=np.uint8), 12)
    run = _Run()
    calls = {"n": 0}

    def _upload(_image: np.ndarray) -> bool:
        calls["n"] += 1
        if calls["n"] == 1:
            live.write(np.ones((2, 2, 3), dtype=np.uint8), 12)
            return False
        run.clear()
        return True

    clock = {"t": 0.0}

    def _monotonic() -> float:
        return clock["t"]

    def _sleep(seconds: float) -> None:
        clock["t"] += seconds

    try:
        with (
            patch.object(thumbs_runner, "upload_thumbnail", side_effect=_upload),
            patch.object(thumbs_runner.time, "sleep", side_effect=_sleep),
            patch.object(thumbs_runner.time, "monotonic", side_effect=_monotonic),
        ):
            thumbs_runner.run_thumbs_worker(live.name, run)  # type: ignore[arg-type]

        assert calls["n"] == 2
        assert clock["t"] >= thumbs_runner._RETRY_S
    finally:
        live.close()
        live.unlink()
