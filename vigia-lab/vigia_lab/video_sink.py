"""Gravação do vídeo bruto numa thread própria (não derruba o fps do pose).

MJPG em .avi: barato em CPU e funciona no OpenCV do Windows sem codec extra.
Se a fila encher, o frame é descartado e contado em `drops` (vira aviso no
semáforo). O container leva o fps nominal; o tempo real fica em `t_wall` do
`_raw.npz` — o reprocessamento NÃO deve confiar no fps do arquivo.
"""

from __future__ import annotations

import queue
import threading
from pathlib import Path

import numpy as np


class VideoSink:
    def __init__(self, path: Path, fps: float, size: tuple[int, int], maxsize: int = 90) -> None:
        import cv2

        path.parent.mkdir(parents=True, exist_ok=True)
        self._writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"MJPG"), fps, size)
        if not self._writer.isOpened():
            raise RuntimeError(f"não foi possível abrir o VideoWriter em {path}")
        self._size = size
        self._queue: queue.Queue[np.ndarray | None] = queue.Queue(maxsize=maxsize)
        self.drops = 0
        self.written = 0
        self._thread = threading.Thread(target=self._run, name="lab-video", daemon=True)
        self._thread.start()

    def write(self, image: np.ndarray) -> None:
        try:
            self._queue.put_nowait(image.copy())
        except queue.Full:
            self.drops += 1

    def _run(self) -> None:
        while True:
            item = self._queue.get()
            if item is None:
                return
            h, w = item.shape[:2]
            if (w, h) != self._size:
                import cv2

                item = cv2.resize(item, self._size)
            self._writer.write(item)
            self.written += 1

    def close(self) -> None:
        self._queue.put(None)
        self._thread.join(timeout=10)
        self._writer.release()
