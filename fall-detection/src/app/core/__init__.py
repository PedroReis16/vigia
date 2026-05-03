"""
Tratamento de informações de movimento e queda

Pacote para tratamento das informações capturadas pelo sistema de movimento, aplicando os devidos tratamentos para a aplicação de algoritmos de reconhecimento das quedas.
"""

from .frame_consumer import run_frame_consumer
from .runner import run_analysis

__all__ = ["run_analysis", "run_frame_consumer"]