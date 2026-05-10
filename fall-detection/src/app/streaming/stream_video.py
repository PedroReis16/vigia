"""Envio de frames BGR em bruto para FFmpeg (RTMP/FLV)."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys

import numpy as np


def _ffmpeg_executable() -> str:
    """Caminho do binário FFmpeg: ``FFMPEG_BIN`` ou nome no ``PATH`` (``ffmpeg``)."""
    raw = (os.environ.get("FFMPEG_BIN") or "").strip() or "ffmpeg"
    if os.sep in raw or (len(raw) > 2 and raw[1] == ":"):
        return raw
    found = shutil.which(raw)
    if found is None:
        raise RuntimeError(
            "ffmpeg nao encontrado no PATH. Instale o pacote ffmpeg no sistema "
            "(ex.: apt install ffmpeg / apk add ffmpeg) ou defina FFMPEG_BIN com o caminho absoluto do executavel."
        )
    return found


def _ffmpeg_subprocess_env() -> dict[str, str]:
    """Ambiente para executar o FFmpeg do sistema quando a app corre sob PyInstaller.

    O bootloader acrescenta ``_internal/`` a ``LD_LIBRARY_PATH``. Se o subprocesso
    herdar isso, o FFmpeg carrega ``libstdc++.so.6`` do bundle em vez da do OS e
    falha com ``GLIBCXX_*`` / ``CXXABI_*`` em bibliotecas do sistema (libav*, etc.).
    """
    env = os.environ.copy()
    ld = env.get("LD_LIBRARY_PATH")
    if not ld:
        return env

    meipass = getattr(sys, "_MEIPASS", None)
    me_norm = os.path.normpath(meipass) if meipass else None

    parts_out: list[str] = []
    for p in ld.split(os.pathsep):
        q = p.strip()
        if not q:
            continue
        if "_internal" in q.replace("\\", "/"):
            continue
        q_norm = os.path.normpath(q)
        if me_norm and (q_norm == me_norm or q_norm.startswith(me_norm + os.sep)):
            continue
        parts_out.append(p)

    if parts_out:
        env["LD_LIBRARY_PATH"] = os.pathsep.join(parts_out)
    else:
        env.pop("LD_LIBRARY_PATH", None)
    return env


class _RtmpStreamState:
    __slots__ = ("process", "frame_size")

    def __init__(self) -> None:
        self.process: subprocess.Popen | None = None
        self.frame_size: tuple[int, int] | None = None


_rtmp_stream_state = _RtmpStreamState()


def _start_ffmpeg(width: int, height: int, rtmp_url: str) -> subprocess.Popen:
    cmd = [
        _ffmpeg_executable(),
        "-y",
        "-f",
        "rawvideo",
        "-vcodec",
        "rawvideo",
        "-pix_fmt",
        "bgr24",
        "-s",
        f"{width}x{height}",
        "-r",
        "30",
        "-i",
        "-",
        "-c:v",
        "libx264",
        "-preset",
        "ultrafast",
        "-tune",
        "zerolatency",
        "-pix_fmt",
        "yuv420p",
        "-f",
        "flv",
        rtmp_url,
    ]
    return subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        env=_ffmpeg_subprocess_env(),
    )


def stream_video(frame: np.ndarray, rtmp_url: str) -> None:
    h, w = frame.shape[:2]
    state = _rtmp_stream_state

    if state.process is None:
        state.process = _start_ffmpeg(w, h, rtmp_url)
        state.frame_size = (w, h)

    # Segurança: evita corrupção se frame vier com stride/layout diferente
    frame = np.ascontiguousarray(frame)

    if state.process.stdin is None:
        raise RuntimeError("FFmpeg stdin indisponível")

    state.process.stdin.write(frame.tobytes())
