"""Loop principal de vídeo: câmera, pose assíncrono, stream e preview."""

from app.capture.loop.capture_loop import run_capture_loop
from app.capture.loop.capture_loop_context import CaptureLoopContext

__all__ = ["CaptureLoopContext", "run_capture_loop"]
