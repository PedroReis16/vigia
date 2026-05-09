"""Envio de frames BGR em bruto para FFmpeg (RTMP/FLV)."""

from __future__ import annotations

import subprocess

import numpy as np

class _RtmpStreamState:
    __slots__ = ("process", "frame_size")

    def __init__(self) -> None:
        self.process: subprocess.Popen | None = None
        self.frame_size: tuple[int, int] | None = None


_rtmp_stream_state = _RtmpStreamState()


def _start_ffmpeg(width: int, height: int, rtmp_url: str) -> subprocess.Popen:
    cmd = [
        "ffmpeg", "-y",
        "-f", "rawvideo",
        "-vcodec", "rawvideo",
        "-pix_fmt", "bgr24",
        "-s", f"{width}x{height}",
        "-r", "30",
        "-i", "-",
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-tune", "zerolatency",
        "-pix_fmt", "yuv420p",
        "-f", "flv",
        rtmp_url,
    ]
    return subprocess.Popen(cmd, stdin=subprocess.PIPE)

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