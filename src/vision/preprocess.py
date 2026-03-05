import numpy as np


class FeatureExtractor:
    def from_vector(self, raw_values: list[float]) -> list[float]:
        if not raw_values:
            return []

        data = np.array(raw_values, dtype=float)
        scaled = np.clip(data, 0.0, 1.0)
        return scaled.tolist()
