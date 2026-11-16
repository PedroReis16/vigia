"""Classificadores de queda (math e gru)."""

from .factory import create_classifier
from .math_classifier import MathFallClassifier

__all__ = ["MathFallClassifier", "create_classifier"]
