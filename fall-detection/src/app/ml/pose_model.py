from ultralytics import YOLO
import numpy as np

class PoseModel:
    def __init__(self, model_path: str, device: str = "cpu"):
            self.model = YOLO(model_path)
            self.device = device

    def predict(self, frame: np.ndarray)->np.ndarray:
        return self.model.predict(frame, conf=0.75, verbose=False, device=self.device)