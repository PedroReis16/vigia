from dataclasses import dataclass

import numpy as np


@dataclass(slots=True)
class ModelPrediction:
    fall_detected: bool
    confidence: float


class BaselineFallDetector:
    def __init__(self, threshold: float = 0.65) -> None:
        self.threshold = threshold

    def predict(self, features: list[float]) -> ModelPrediction:
        if not features:
            return ModelPrediction(fall_detected=False, confidence=0.0)

        normalized = np.clip(np.array(features, dtype=float), 0.0, 1.0)
        confidence = float(normalized.mean())
        return ModelPrediction(
            fall_detected=confidence >= self.threshold,
            confidence=confidence,
        )
