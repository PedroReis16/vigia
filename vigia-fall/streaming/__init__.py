"""
Módulo de streaming RTMP isolado (processo sob demanda via IPC).
"""

from .stream_runner import run_stream

__all__ = ["run_stream"]
