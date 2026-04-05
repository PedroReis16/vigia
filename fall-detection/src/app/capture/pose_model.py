from ultralytics import YOLO
import numpy as np
from app.capture.frame_data import PersonData, BodyData

class PoseModel:
    
    _TRACKED_KEYPOINTS: tuple[tuple[str, int], ...] = (
        ("nariz", 0),
        ("ombro_esq", 5),
        ("ombro_dir", 6),
    )

    _CONF_MIN: float = 0.75

    def __init__(self, model_path: str, device: str = "cpu"):
            self.model = YOLO(model_path)
            self.device = device

    def _get_person_ids_from_result(self, result, data: np.ndarray) -> list[int]:
        boxes = result.boxes
        ids_tensor = getattr(boxes, "id", None)

        if ids_tensor is not None and len(ids_tensor) >= len(data):
            return [int(ids_tensor[i].item()) for i in range(len(data))]
        return list[int](range(len(data)))

    def capture_frame(self, frame: np.ndarray) -> list[PersonData]:
        """
        Capture a frame with YOLO pose model and return the person keypoints data.
        """
        
        results = self.model.track(frame, conf=self._CONF_MIN, verbose=False, device=self.device, persist=True)

        frame_results: list[PersonData] = []

        for result in results:
            kpts = result.keypoints
            if kpts is None or kpts.data is None:
                continue
            data = kpts.data
            if len(data) == 0:
                continue

            person_ids = self._get_person_ids_from_result(result, data)

            for person_id, person in zip(person_ids, data):
                body_data: list[BodyData] = []

                for label, idx in self._TRACKED_KEYPOINTS:
                    x, y, conf = person[idx]
                    if conf < self._CONF_MIN:
                        continue
                    cx, cy = float(x.item()), float(y.item())
                    body_data.append(BodyData(label, cx, cy, conf))

                frame_results.append(PersonData(person_id, body_data))

        return frame_results

    