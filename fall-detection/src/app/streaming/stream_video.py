import subprocess
import numpy as np


# Configure FFmpeg to read raw video from stdin and stream via RTMP
rtmp_url = "rtmp://localhost:1935/live/cam1"
command = [
    'ffmpeg', '-y', '-f', 'rawvideo', '-vcodec', 'rawvideo',
    '-pix_fmt', 'bgr24', '-s', f"{300}x{300}", '-r', str(30),
    '-i', '-', '-c:v', 'libx264', '-pix_fmt', 'yuv420p',
    '-preset', 'ultrafast', '-f', 'flv', rtmp_url
]

process = subprocess.Popen(command, stdin=subprocess.PIPE)


def stream_video(frame: np.ndarray) -> None:
    """Stream the video to the network."""
    if process.stdin is None:
        raise RuntimeError("FFmpeg process stdin is not available.")
    process.stdin.write(frame.tobytes())