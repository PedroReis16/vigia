"""Workers em thread: gravação de PNG no disco e envio de JPEG (TCP ou HTTP)."""

from __future__ import annotations

import queue
import socket
import struct
import threading
import time
import urllib.error
import urllib.request
from typing import Any

import cv2


class FrameSaveWorker:
    """Fila de gravação: o loop principal só enfileira; imwrite não bloqueia read/show."""

    def __init__(self, maxsize: int = 8) -> None:
        self._q: queue.Queue[tuple[str, Any] | None] | None = None
        self._thread: threading.Thread | None = None
        self._maxsize = maxsize

    def start(self) -> None:
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
        if self._q is not None:
            self._q.put(None)
        if self._thread is not None:
            self._thread.join(timeout=5.0)
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


class StreamOutWorker:
    """Envia frames JPEG para ingest HTTP ou TCP (4 bytes LE + tamanho + payload)."""

    def __init__(self) -> None:
        self._q: queue.Queue[bytes | None] | None = None
        self._thread: threading.Thread | None = None

    def start_tcp(self, host: str, port: int) -> None:
        self._start_queue(maxsize=8)
        assert self._q is not None

        def worker() -> None:
            sock: socket.socket | None = None
            while True:
                job = self._q.get()
                if job is None:
                    break
                payload = job
                while True:
                    try:
                        if sock is None:
                            sock = socket.create_connection((host, port), timeout=2.0)
                            try:
                                sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                            except OSError:
                                pass
                        header = struct.pack("<I", len(payload))
                        sock.sendall(header + payload)
                        break
                    except OSError:
                        if sock is not None:
                            try:
                                sock.close()
                            except OSError:
                                pass
                            sock = None
                        time.sleep(0.25)
            if sock is not None:
                try:
                    sock.close()
                except OSError:
                    pass

        self._thread = threading.Thread(target=worker, name="tcp-stream", daemon=True)
        self._thread.start()

    def start_http(self, url: str, token: str) -> None:
        self._start_queue(maxsize=2)
        assert self._q is not None

        def worker() -> None:
            while True:
                job = self._q.get()
                if job is None:
                    break
                while True:
                    try:
                        req = urllib.request.Request(url, data=job, method="POST")
                        req.add_header("Content-Type", "application/octet-stream")
                        if token:
                            req.add_header("X-Vigia-Ingest-Token", token)
                        with urllib.request.urlopen(req, timeout=20) as resp:
                            if resp.status not in (200, 204):
                                time.sleep(0.25)
                                continue
                        break
                    except (OSError, urllib.error.HTTPError):
                        time.sleep(0.25)

        self._thread = threading.Thread(target=worker, name="http-ingest", daemon=True)
        self._thread.start()

    def _start_queue(self, maxsize: int) -> None:
        if self._thread is not None:
            return
        self._q = queue.Queue(maxsize=maxsize)

    def stop(self) -> None:
        if self._q is not None:
            self._q.put(None)
        if self._thread is not None:
            self._thread.join(timeout=5.0)
            self._thread = None
            self._q = None

    def send_frame(self, frame: Any) -> None:
        if self._q is None:
            return
        ok, buf = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
        if not ok:
            return
        payload = buf.tobytes()
        try:
            self._q.put_nowait(payload)
        except queue.Full:
            try:
                self._q.get_nowait()
            except queue.Empty:
                pass
            try:
                self._q.put_nowait(payload)
            except queue.Full:
                pass


def optional_stream_worker(
    stream_ingest_url: str,
    stream_ingest_token: str,
    stream_target: tuple[str, int] | None,
) -> StreamOutWorker | None:
    """Cria e inicia worker de saída conforme URL HTTP ou alvo TCP."""
    w = StreamOutWorker()
    if stream_ingest_url:
        w.start_http(stream_ingest_url, stream_ingest_token)
        return w
    if stream_target:
        w.start_tcp(stream_target[0], stream_target[1])
        return w
    return None
