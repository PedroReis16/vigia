"""
Constantes de captura
"""

TRACKED_KPTS = {0, 5, 6, 11, 12, 13, 14, 15, 16}
MAX_MISSED_FRAMES = 15  # limpa o tracker se sumir por N frames (evita leak de memória)
MIN_KPT_CONF = 0.3  # abaixo disso o keypoint é tratado como ausente (só predição)


# Suavização do scale de normalização (torso)
SCALE_EMA_ALPHA = 0.1    #peso do frame atual; menor = mais suave; EMA = Media Movel Exponencial
MIN_TORSO_SCALE = 1e-3   #evita divisão por scale ~0


# trunk_angle = inclinação do tronco
# pca_ratio = alongmaneto da silhueta
# pca_angle = orientação do eixo principal (rad)
