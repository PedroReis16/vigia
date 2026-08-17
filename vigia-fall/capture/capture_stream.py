"""
Módulo para o processo de streaming de vídeo
"""

from __future__ import annotations

import os
import queue
import shutil
import subprocess
import sys
import threading
import time
from urllib.parse import urlparse

import numpy as np

from shared import (
    get_device_identity,
    get_network_settings,
    get_settings,
    set_stream_status,
)

_SHUTDOWN = object()
_RECONNECT_BACKOFF_S = 2.0
_MAX_RECONNECT_ATTEMPTS = 5
_BUNDLE_PATH_MARKERS = ("/_internal", "_internal/")


def _is_bundle_lib_path(path: str) -> bool:
    if not path:
        return False
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass and (path == meipass or path.startswith(f"{meipass}/")):
        return True
    return any(marker in path for marker in _BUNDLE_PATH_MARKERS)


def _scrub_path_env(value: str) -> str | None:
    parts = [p for p in value.split(":") if p and not _is_bundle_lib_path(p)]
    return ":".join(parts) if parts else None


def _system_subprocess_env() -> dict[str, str]:
    """
    Ambiente para binários do sistema (ex.: ffmpeg).

    O bootloader do PyInstaller injeta `_internal` em LD_LIBRARY_PATH; o ffmpeg
    do apt passa a carregar o libstdc++ do bundle (mais antigo) e falha com
    GLIBCXX_/CXXABI_ not found. Remove paths do bundle e restaura o valor
    original quando existir (LD_LIBRARY_PATH_ORIG).
    """
    env = os.environ.copy()

    for key in ("LD_LIBRARY_PATH", "LD_PRELOAD", "LIBRARY_PATH"):
        env.pop(f"{key}_ORIG", None)
        current = env.get(key)
        if current is None:
            continue
        cleaned = _scrub_path_env(current)
        if cleaned is None:
            env.pop(key, None)
        else:
            env[key] = cleaned

    # Preferência: valor original do processo pai (antes do bootloader).
    lp_orig = os.environ.get("LD_LIBRARY_PATH_ORIG")
    if lp_orig is not None:
        cleaned_orig = _scrub_path_env(lp_orig)
        if cleaned_orig is None:
            env.pop("LD_LIBRARY_PATH", None)
        else:
            env["LD_LIBRARY_PATH"] = cleaned_orig
    else:
        # Sem original: não herdar o LD_LIBRARY_PATH do frozen app.
        env.pop("LD_LIBRARY_PATH", None)

    return env


def _ffmpeg_executable() -> str:
    """Resolve o ffmpeg do sistema, evitando qualquer binário do bundle."""
    for candidate in ("/usr/bin/ffmpeg", "/bin/ffmpeg"):
        if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
            return candidate
    found = shutil.which("ffmpeg", path="/usr/bin:/bin:/usr/local/bin")
    if found:
        return found
    return "ffmpeg"


def _rtmp_publish_url(api_base_url: str, device_id: str) -> str:
    """
    Monta a URL RTMP de publicação.

    MediaMTX local escuta RTMP plain em :1935 (não RTMPS).
    """
    _ = urlparse(api_base_url)
    if api_base_url.startswith("https"):
        protocol = "rtmps"
    else:
        protocol = "rtmp"

    if api_base_url.startswith("https"):
        host = api_base_url.split("://")[1].split(":")[0]
    else:
        host = (
            f"{api_base_url.split("://")[1].split(":")[0]}:{1935}" or "localhost:1935"
        )

    return f"{protocol}://{host}/live/{device_id}"


class RtmpPublisher:
    """
    Mantém um processo FFmpeg persistente para publicar frames BGR via RTMP.
    """

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
        """
        Inicia (ou reinicia) o publisher com a geometria e destino informados.
        """
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
            "ultrafast",
            "-tune",
            "zerolatency",
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
            "-f",
            "flv",
            url,
        ]

        self._process = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            bufsize=0,
            env=_system_subprocess_env(),
            close_fds=True,
        )
        self._width = width
        self._height = height
        self._fps = fps
        self._url = url

    def write(self, frame: np.ndarray) -> None:
        """
        Envia um frame BGR para o encoder.
        """
        if self._process is None or self._process.stdin is None:
            raise RuntimeError("Publisher RTMP não iniciado")

        if self._process.poll() is not None:
            detail = self._consume_stderr(self._process)
            self.stop()
            raise RuntimeError(
                "Processo FFmpeg encerrou durante a publicação"
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
                + (f": {detail}" if detail else " (destino RTMP inacessível?)")
            ) from exc

    def stop(self) -> None:
        """
        Encerra o processo FFmpeg e libera recursos.
        """
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


class StreamWorker:
    """
    Consome frames em thread dedicada para não bloquear o loop de captura.
    """

    def __init__(self, queue_size: int = 2) -> None:
        self._queue: queue.Queue[np.ndarray | object] = queue.Queue(maxsize=queue_size)
        self._publisher = RtmpPublisher()
        self._thread: threading.Thread | None = None
        self._lock = threading.Lock()
        self._active = False
        self._fps = 0
        self._url = ""
        self._next_attempt_at = 0.0
        self._failures = 0

    @property
    def is_active(self) -> bool:
        return self._active or self._publisher.is_running

    def submit(self, frame: np.ndarray) -> None:
        """
        Enfileira uma cópia do frame. Se a fila estiver cheia, descarta o mais antigo.
        """
        self._ensure_started()
        self._active = True

        # OpenCV reutiliza o buffer no próximo cap.read(); a cópia é necessária.
        payload = frame.copy()

        try:
            self._queue.put_nowait(payload)
        except queue.Full:
            try:
                self._queue.get_nowait()
            except queue.Empty:
                pass
            try:
                self._queue.put_nowait(payload)
            except queue.Full:
                pass

    def stop(self) -> None:
        """
        Interrompe a publicação e esvazia a fila, mantendo a thread viva.
        """
        self._active = False
        self._next_attempt_at = 0.0
        self._failures = 0
        self._drain_queue()
        with self._lock:
            self._publisher.stop()

    def shutdown(self) -> None:
        """
        Encerra publicação e a thread do worker.
        """
        self.stop()
        try:
            self._queue.put_nowait(_SHUTDOWN)
        except queue.Full:
            self._drain_queue()
            try:
                self._queue.put_nowait(_SHUTDOWN)
            except queue.Full:
                pass

        thread = self._thread
        if thread is not None and thread.is_alive():
            thread.join(timeout=3)
        self._thread = None

    def _ensure_started(self) -> None:
        with self._lock:
            if self._thread is not None and self._thread.is_alive():
                return
            self._thread = threading.Thread(
                target=self._run,
                name="rtmp-stream",
                daemon=True,
            )
            self._thread.start()

    def _drain_queue(self) -> None:
        while True:
            try:
                self._queue.get_nowait()
            except queue.Empty:
                break

    def _resolve_target(self) -> tuple[int, str]:
        if not self._url or not self._fps:
            settings = get_settings()
            self._fps = settings.frame_rate
            self._url = _rtmp_publish_url(
                get_network_settings().api_base_url,
                get_device_identity().device_id,
            )
        return self._fps, self._url

    def _publish(self, frame: np.ndarray) -> None:
        height, width = frame.shape[:2]
        width -= width % 2
        height -= height % 2
        if height == 0 or width == 0:
            return

        frame = np.ascontiguousarray(frame[:height, :width])
        fps, url = self._resolve_target()

        with self._lock:
            if not self._active:
                return
            self._publisher.start(width, height, fps, url)
            self._publisher.write(frame)

    def _run(self) -> None:
        while True:
            try:
                item = self._queue.get(timeout=0.2)
            except queue.Empty:
                continue

            if item is _SHUTDOWN:
                with self._lock:
                    self._publisher.stop()
                break

            if not self._active:
                continue

            now = time.monotonic()
            if now < self._next_attempt_at:
                continue

            try:
                self._publish(item)
            except Exception as exc:
                self._handle_publish_failure(exc)
            else:
                if self._failures:
                    print("Publicação RTMP restabelecida")
                self._failures = 0

    def _handle_publish_failure(self, exc: Exception) -> None:
        self._failures += 1
        with self._lock:
            self._publisher.stop()

        if self._failures >= _MAX_RECONNECT_ATTEMPTS:
            print(
                f"Streaming encerrado após {_MAX_RECONNECT_ATTEMPTS} falhas consecutivas: {exc}"
            )
            try:
                set_stream_status(False)
            except RuntimeError:
                pass
            self.stop()
            return

        backoff = _RECONNECT_BACKOFF_S * self._failures
        self._next_attempt_at = time.monotonic() + backoff
        print(
            f"Erro ao publicar frame no RTMP "
            f"(tentativa {self._failures}/{_MAX_RECONNECT_ATTEMPTS}, "
            f"nova em {backoff:.1f}s): {exc}"
        )


_worker = StreamWorker(queue_size=2)


def stream_video(frame: np.ndarray) -> None:
    """
    Enfileira o frame para publicação RTMP em thread dedicada.
    """
    if frame is None or frame.size == 0:
        return
    _worker.submit(frame)


def is_streaming() -> bool:
    """
    Indica se o streaming está ativo (fila/publisher).
    """
    return _worker.is_active


def stop_stream() -> None:
    """
    Interrompe a publicação RTMP, se estiver ativa.
    """
    _worker.stop()


def shutdown_stream() -> None:
    """
    Encerra o worker de streaming por completo.
    """
    _worker.shutdown()
