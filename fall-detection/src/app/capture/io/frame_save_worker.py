"""Worker em thread que grava PNG no disco a partir de uma fila."""

from __future__ import annotations

import queue
import threading
from typing import Any

import cv2


class FrameSaveWorker:
    """Fila de gravação: o loop principal só enfileira; imwrite não bloqueia read/show."""

    def __init__(self, maxsize: int = 8) -> None:
        self._q: queue.Queue[tuple[str, Any] | None] | None = None
        self._thread: threading.Thread | None = None
        self._maxsize = maxsize

    def start(self) -> None:
        """Inicia thread que consome a fila e grava PNG com `cv2.imwrite`."""
        if self._thread is not None:
            return

        q: queue.Queue[tuple[str, Any] | None] = queue.Queue(maxsize=self._maxsize)

        def worker() -> None:
            while True:
                job = q.get()
                if job is None:
                    break
                path, img = job
                cv2.imwrite(path, img)

        self._q = q
        self._thread = threading.Thread(target=worker, name="frame-saver", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Sinaliza fim ao worker e aguarda encerramento (curto timeout)."""
        if self._q is not None:
            # put(None) bloqueia se a fila estiver cheia e o worker estiver lento (imwrite).
            while True:
                try:
                    self._q.put_nowait(None)
                    break
                except queue.Full:
                    try:
                        self._q.get_nowait()
                    except queue.Empty:
                        pass
        if self._thread is not None:
            self._thread.join(timeout=0.5)
            self._thread = None
            self._q = None

    def put_copy(self, path: str, roi: Any) -> bool:
        """Enfileira cópia do ROI. Retorna False se a fila estiver cheia (backpressure)."""
        if self._q is None:
            return False
        try:
            self._q.put_nowait((path, roi.copy()))
            return True
        except queue.Full:
            return False
