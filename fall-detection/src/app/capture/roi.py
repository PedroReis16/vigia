"""Região de interesse central no frame (margem percentual)."""

from __future__ import annotations

from typing import Any


def central_roi(
    frame: Any, margin_ratio: float = 0.05
) -> tuple[Any, tuple[int, int, int, int]]:
    """
    Retorna (roi, (x1, y1, x2, y2)) com margem relativa em cada lado.
    """
    height, width = frame.shape[:2]
    x1 = int(width * margin_ratio)
    x2 = int(width * (1.0 - margin_ratio))
    y1 = int(height * margin_ratio)
    y2 = int(height * (1.0 - margin_ratio))
    roi = frame[y1:y2, x1:x2]
    return roi, (x1, y1, x2, y2)
