"""Sessão de gravação de frames em disco (pastas por segundo decorrido)."""

from __future__ import annotations

import os
import time
from typing import Any

import cv2

from app.capture.io.workers import FrameSaveWorker


def frame_dir_for_elapsed_seconds(fr_dir: str, elapsed_sec: int) -> str:
    """Uma pasta por segundo decorrido desde o início (000000, 000001, ...)."""
    d = os.path.join(fr_dir, f"{elapsed_sec:06d}")
    os.makedirs(d, exist_ok=True)
    return d


class DiskFrameCapture:
    """Contadores de sessão + gravação via fila ou imwrite síncrono."""

    def __init__(
        self,
        frames_dir: str,
        saver: FrameSaveWorker | None,
        session_start: float | None = None,
    ) -> None:
        self._frames_dir = frames_dir
        self._saver = saver
        self._t0 = session_start if session_start is not None else time.monotonic()
        self._second_bucket = -1
        self._frame_in_second = 0
        self._item = 0
        self._last_auto_capture = time.monotonic()

    def maybe_auto_capture(self, roi: Any, now: float, interval: float | None) -> None:
        """Dispara `capture_frame` quando o intervalo desde a última captura foi atingido."""
        if interval is None:
            return
        if now - self._last_auto_capture >= interval:
            self.capture_frame(roi, now)

    def capture_frame(self, roi: Any, now: float) -> None:
        """Grava um PNG no bucket do segundo atual (fila assíncrona ou `imwrite`)."""
        self._last_auto_capture = now
        elapsed_sec = int(now - self._t0)

        if elapsed_sec != self._second_bucket:
            self._second_bucket = elapsed_sec
            self._frame_in_second = 0
        self._frame_in_second += 1
        self._item += 1
        out_dir = frame_dir_for_elapsed_seconds(self._frames_dir, elapsed_sec)
        path = os.path.join(out_dir, f"frame_{self._frame_in_second:04d}.png")

        if self._saver is not None:
            if not self._saver.put_copy(path, roi):
                self._item -= 1
                self._frame_in_second -= 1
        else:
            ok = cv2.imwrite(path, roi)
            if not ok:
                self._item -= 1
                self._frame_in_second -= 1
