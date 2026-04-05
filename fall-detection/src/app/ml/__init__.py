"""
Modelos e pós-processamento (ex.: YOLO, pose, métricas).

Coloque aqui inferência, conversão de tensores e cálculos derivados dos keypoints.
O loop em `app.runtime` pode importar e chamar funções deste pacote quando existirem.
"""

from .runner import run_analysis

__all__ = ["run_analysis"]