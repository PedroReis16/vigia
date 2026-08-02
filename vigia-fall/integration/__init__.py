"""
Módulo de integração do dispositivo
"""

from .integration_runner import initialize_device
from .fiware_runner import run_fiware

__all__ = ["initialize_device", "run_fiware"]
