"""Publicação RTMP via FFmpeg (contrato MediaMTX /live/{deviceId})."""

from __future__ import annotations

import logging
import os
import shutil
import subprocess
import sys
import threading
import time
from urllib.parse import urlparse

import numpy as np

from worker.frame_bus import FrameBus

logger = logging.getLogger(__name__)

_RECONNECT_BACKOFF_S = 2.0


def _ffmpeg_executable() -> str:
    unix_candidates = (
        "/usr/bin/ffmpeg",
        "/bin/ffmpeg",
        "/usr/local/bin/ffmpeg",
        "/opt/homebrew/bin/ffmpeg",
    )
    if sys.platform != "win32":
        for candidate in unix_candidates:
            if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
                return candidate

    for name in ("ffmpeg.exe", "ffmpeg"):
        found = shutil.which(name)
        if found:
            return found
    return "ffmpeg.exe" if sys.platform == "win32" else "ffmpeg"


def rtmp_publish_url(stream_ingest_url: str, device_id: str) -> str:
    base_url = (stream_ingest_url or "").strip()
    parsed = urlparse(base_url)
    if parsed.scheme not in {"rtmp", "rtmps"} or not parsed.hostname:
        raise ValueError(f"URL de ingestão RTMP inválida: {stream_ingest_url}")
    if parsed.path not in {"", "/"} or parsed.params or parsed.query or parsed.fragment:
        raise ValueError(
            "URL de ingestão RTMP deve conter somente esquema, host e porta"
        )
    return f"{base_url.rstrip('/')}/live/{device_id}"


class RtmpPublisher:
    def __init__(self) -> None:
        self._process: subprocess.Popen[bytes] | None = None
        self._width = 0
        self._height = 0
        self._fps = 0
        self._url = ""

    @property
    def is_running(self) -> bool:
        return self._process is not None and self._process.poll() is None

    def start(self, width: int, height: int, fps: int, url: str) -> None:
        if (
            self.is_running
            and self._width == width
            and self._height == height
            and self._fps == fps
            and self._url == url
        ):
            return

        self.stop()
        command = [
            _ffmpeg_executable(),
            "-hide_banner",
            "-loglevel",
            "error",
            "-fflags",
            "nobuffer",
            "-flags",
            "low_delay",
            "-f",
            "rawvideo",
            "-pix_fmt",
            "bgr24",
            "-s",
            f"{width}x{height}",
            "-r",
            str(fps),
            "-i",
            "pipe:0",
            "-an",
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-tune",
            "zerolatency",
            "-crf",
            "18",
            "-profile:v",
            "baseline",
            "-pix_fmt",
            "yuv420p",
            "-g",
            str(fps),
            "-keyint_min",
            str(fps),
            "-bf",
            "0",
            "-muxdelay",
            "0",
            "-muxpreload",
            "0",
            "-f",
            "flv",
            url,
        ]
        popen_kwargs: dict = {
            "stdin": subprocess.PIPE,
            "stdout": subprocess.DEVNULL,
            "stderr": subprocess.PIPE,
            "bufsize": 0,
        }
        if sys.platform != "win32":
            popen_kwargs["close_fds"] = True

        self._process = subprocess.Popen(command, **popen_kwargs)
        self._width = width
        self._height = height
        self._fps = fps
        self._url = url
        logger.info("RTMP a publicar em %s (%sx%s @ %sfps)", url, width, height, fps)

    def write(self, frame: np.ndarray) -> None:
        if self._process is None or self._process.stdin is None:
            raise RuntimeError("Publisher RTMP não iniciado")
        if self._process.poll() is not None:
            detail = self._consume_stderr(self._process)
            self.stop()
            raise RuntimeError(
                "Processo FFmpeg encerrou"
                + (f": {detail}" if detail else "")
            )
        try:
            self._process.stdin.write(frame.tobytes())
            self._process.stdin.flush()
        except (BrokenPipeError, OSError) as exc:
            detail = self._consume_stderr(self._process)
            self.stop()
            raise RuntimeError(
                "Pipe do FFmpeg quebrado"
                + (f": {detail}" if detail else "")
            ) from exc

    def stop(self) -> None:
        process = self._process
        self._process = None
        self._width = 0
        self._height = 0
        self._fps = 0
        self._url = ""
        if process is None:
            return
        if process.stdin is not None:
            try:
                process.stdin.close()
            except OSError:
                pass
        try:
            process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=1)
        finally:
            self._consume_stderr(process)

    @staticmethod
    def _consume_stderr(process: subprocess.Popen[bytes]) -> str:
        if process.stderr is None:
            return ""
        try:
            raw = process.stderr.read()
        except OSError:
            return ""
        if not raw:
            return ""
        return raw.decode(errors="replace").strip()


def run_rtmp_loop(
    bus: FrameBus,
    stream_on: threading.Event,
    stop_event: threading.Event,
    *,
    stream_ingest_url: str,
    device_id: str,
) -> None:
    """Publica frames no MediaMTX enquanto ``stream_on`` estiver ativo."""
    publisher = RtmpPublisher()
    url = rtmp_publish_url(stream_ingest_url, device_id)
    next_attempt = 0.0

    try:
        while not stop_event.is_set():
            if not stream_on.is_set():
                if publisher.is_running:
                    publisher.stop()
                    logger.info("stream_off — RTMP parado")
                stop_event.wait(0.2)
                continue

            frame = bus.latest()
            if frame is None:
                stop_event.wait(0.05)
                continue

            height, width = frame.shape[:2]
            fps = max(1, int(round(bus.fps)))
            now = time.monotonic()
            try:
                if not publisher.is_running:
                    if now < next_attempt:
                        stop_event.wait(0.1)
                        continue
                    publisher.start(width, height, fps, url)
                publisher.write(frame)
            except (RuntimeError, ValueError, OSError) as exc:
                logger.warning("RTMP falhou: %s", exc)
                publisher.stop()
                next_attempt = time.monotonic() + _RECONNECT_BACKOFF_S

            # ritmo aproximado do playback
            stop_event.wait(max(0.01, 1.0 / max(bus.fps, 1.0)))
    finally:
        publisher.stop()
        logger.info("Loop RTMP terminado")
