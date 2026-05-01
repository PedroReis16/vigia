import subprocess
import numpy as np

_process = None
_frame_size = None  # (w, h)

def _start_ffmpeg(width: int, height: int) -> subprocess.Popen:
    rtmp_url = "rtmp://localhost:1935/live/cam1"
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

def stream_video(frame: np.ndarray) -> None:
    global _process, _frame_size

    h, w = frame.shape[:2]

    if _process is None:
        _process = _start_ffmpeg(w, h)
        _frame_size = (w, h)

    # Segurança: evita corrupção se frame vier com stride/layout diferente
    frame = np.ascontiguousarray(frame)

    if _process.stdin is None:
        raise RuntimeError("FFmpeg stdin indisponível")

    _process.stdin.write(frame.tobytes())