""" "
Módulo de captura de vídeo
"""

from .runner import run_capture_async
from .frame_processor import process_frame

__all__ = ["run_capture_async", "process_frame"]
