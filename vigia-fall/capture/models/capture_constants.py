"""
Constantes de captura
"""

TRACKED_KPTS = {0, 5, 6, 11, 12, 13, 14, 15, 16}
MAX_MISSED_FRAMES = 15  # limpa o tracker se sumir por N frames (evita leak de memória)
MIN_KPT_CONF = 0.3  # abaixo disso o keypoint é tratado como ausente (só predição)
