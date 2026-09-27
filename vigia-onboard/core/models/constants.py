"""Constantes usadas na filtragem e no classificador matemático."""

TRACKED_KPTS = {0, 5, 6, 11, 12, 13, 14, 15, 16}
MAX_MISSED_FRAMES = 15
MIN_KPT_CONF = 0.3
REQUIRED_JOINTS = (5, 6, 11, 12)

SCALE_EMA_ALPHA = 0.1
MIN_TORSO_SCALE = 1e-3
COM_SHOULDER_WEIGHT = 0.6
