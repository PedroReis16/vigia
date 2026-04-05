"""Worker em thread que envia frames JPEG por TCP ou HTTP."""

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


class StreamOutWorker:
    """Envia frames JPEG para ingest HTTP ou TCP (4 bytes LE + tamanho + payload)."""

    def __init__(self) -> None:
        self._q: queue.Queue[bytes | None] | None = None
        self._thread: threading.Thread | None = None

    def start_tcp(self, host: str, port: int) -> None:
        """Inicia envio JPEG por TCP (header 4 bytes LE + payload)."""
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
        """Inicia POST de JPEG para URL de ingest (com token opcional no header)."""
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
        """Cria fila interna se ainda não houver worker ativo."""
        if self._thread is not None:
            return
        self._q = queue.Queue(maxsize=maxsize)

    def stop(self) -> None:
        """Encerra worker TCP/HTTP de forma não bloqueante quando possível."""
        if self._q is not None:
            # put(None) bloqueia se a fila estiver cheia e o worker estiver em I/O de rede
            # (ex.: urlopen até 20s), travando o encerramento ao pressionar "q".
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

    def send_frame(self, frame: Any) -> None:
        """Codifica frame em JPEG e enfileira (descarta mais antigo se fila cheia)."""
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
