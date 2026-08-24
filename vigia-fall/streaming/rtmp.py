"""
Publicação RTMP via FFmpeg (worker em thread dedicada).
"""

from __future__ import annotations

import logging
import os
import shutil
import subprocess
import sys
import time
from urllib.parse import urlparse

import numpy as np

from shared import (
    get_device_identity,
    get_network_settings,
    set_stream_status,
)

logger = logging.getLogger(__name__)

_RECONNECT_BACKOFF_S = 2.0
_MAX_RECONNECT_ATTEMPTS = 5
_BUNDLE_PATH_MARKERS = (
    "/_internal",
    "_internal/",
    "\\_internal",
    "_internal\\",
)


def _is_bundle_lib_path(path: str) -> bool:
    if not path:
        return False
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        try:
            if os.path.normpath(path) == os.path.normpath(meipass):
                return True
            if os.path.normpath(path).startswith(os.path.normpath(meipass) + os.sep):
                return True
        except (OSError, TypeError, ValueError):
            pass
    return any(marker in path for marker in _BUNDLE_PATH_MARKERS)


def _scrub_path_env(value: str) -> str | None:
    parts = [
        p for p in value.split(os.pathsep) if p and not _is_bundle_lib_path(p)
    ]
    return os.pathsep.join(parts) if parts else None


def _system_subprocess_env() -> dict[str, str]:
    """
    Ambiente para binários do sistema (ex.: ffmpeg).

    No Linux (placa / PyInstaller), o bootloader injeta `_internal` em
    LD_LIBRARY_PATH e o ffmpeg do apt falha com GLIBCXX_/CXXABI_. Em Windows e
    macOS essas variáveis normalmente não existem — devolvemos o env limpo sem
    alterar o PATH do utilizador.
    """
    env = os.environ.copy()

    # Só relevante em Unix; no Windows estes nomes não costumam existir.
    for key in ("LD_LIBRARY_PATH", "LD_PRELOAD", "LIBRARY_PATH", "DYLD_LIBRARY_PATH"):
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
    elif sys.platform.startswith("linux"):
        # Sem original: não herdar o LD_LIBRARY_PATH do frozen app (só Linux).
        env.pop("LD_LIBRARY_PATH", None)

    return env


def _ffmpeg_executable() -> str:
    """
    Resolve o ffmpeg do sistema (Linux, macOS Homebrew, Windows PATH).
    Evita binários do bundle PyInstaller quando possível.
    """
    unix_candidates = (
        "/usr/bin/ffmpeg",
        "/bin/ffmpeg",
        "/usr/local/bin/ffmpeg",  # macOS Intel Homebrew / Linux local
        "/opt/homebrew/bin/ffmpeg",  # macOS Apple Silicon Homebrew
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
        host = f"{api_base_url.split('://')[1].split(':')[0]}:1935" or "localhost:1935"

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
            "-muxdelay",
            "0",
            "-muxpreload",
            "0",
            "-f",
            "flv",
            url,
        ]

        # Windows não permite close_fds=True com redirecionamento de stdin/out/err.
        popen_kwargs: dict = {
            "stdin": subprocess.PIPE,
            "stdout": subprocess.DEVNULL,
            "stderr": subprocess.PIPE,
            "bufsize": 0,
            "env": _system_subprocess_env(),
        }
        if sys.platform != "win32":
            popen_kwargs["close_fds"] = True

        self._process = subprocess.Popen(command, **popen_kwargs)
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


_publisher = RtmpPublisher()
_failures = 0
_next_attempt_at = 0.0


def _resolve_target(stream_fps: int) -> tuple[int, str]:
    url = _rtmp_publish_url(
        get_network_settings().api_base_url,
        get_device_identity().device_id,
    )
    fps = stream_fps if stream_fps > 0 else 30
    return fps, url


def _prepare_frame(frame: np.ndarray) -> np.ndarray | None:
    height, width = frame.shape[:2]
    width -= width % 2
    height -= height % 2
    if height == 0 or width == 0:
        return None
    return np.ascontiguousarray(frame[:height, :width])


def publish_frame(frame: np.ndarray, stream_fps: int) -> None:
    """
    Publica um frame BGR via RTMP (sem fila intermédia).
    """
    global _failures, _next_attempt_at

    if frame is None or frame.size == 0:
        return

    now = time.monotonic()
    if now < _next_attempt_at:
        return

    prepared = _prepare_frame(frame)
    if prepared is None:
        return

    fps, url = _resolve_target(stream_fps)
    try:
        _publisher.start(prepared.shape[1], prepared.shape[0], fps, url)
        _publisher.write(prepared)
    except Exception as exc:
        _handle_publish_failure(exc)
        return

    if _failures:
        logger.info("Publicação RTMP restabelecida")
    _failures = 0


def _handle_publish_failure(exc: Exception) -> None:
    global _failures, _next_attempt_at

    _failures += 1
    _publisher.stop()

    if _failures >= _MAX_RECONNECT_ATTEMPTS:
        logger.error(
            "Streaming encerrado após %s falhas consecutivas: %s",
            _MAX_RECONNECT_ATTEMPTS,
            exc,
        )
        try:
            set_stream_status(False)
        except RuntimeError:
            pass
        return

    backoff = _RECONNECT_BACKOFF_S * _failures
    _next_attempt_at = time.monotonic() + backoff
    logger.warning(
        "Erro ao publicar frame no RTMP "
        "(tentativa %s/%s, nova em %.1fs): %s",
        _failures,
        _MAX_RECONNECT_ATTEMPTS,
        backoff,
        exc,
    )


def shutdown_stream() -> None:
    """
    Encerra o publisher RTMP.
    """
    global _failures, _next_attempt_at

    _publisher.stop()
    _failures = 0
    _next_attempt_at = 0.0
