"""
Worker para processamento assíncrono dos frames capturados
"""

from functools import lru_cache
import queue

import numpy as np  # pyright: ignore[reportMissingImports]

from capture.classifiers import FallClassifier, create_classifier, get_classifier_id
from capture.frame_processor import extract_poses
from integration.fiware_runner import normalize_fall_state, notify_fall
from shared import get_settings


class FrameWorker:
    """
    Worker para processamento assíncrono dos frames capturados
    """

    def __init__(
        self,
        frame_rate: int,
        classifier: FallClassifier | None = None,
    ) -> None:
        self.raw_frame_queue = queue.Queue(maxsize=frame_rate)
        self._classifier = classifier if classifier is not None else create_classifier()
        self._last_published_fall_state: str | None = None

    def __consume_raw_frame(self) -> bool:
        item = self.raw_frame_queue.get()

        if item is None:
            return False

        frame, capture_date = item

        observations = extract_poses(frame, capture_date)
        self.raw_frame_queue.task_done()

        if not observations:
            return True

        decisions = self._classifier.process(observations)
        for decision in decisions:
            print(
                f"Person {decision.person_id}: {decision.label}"
                f"{' ALERT' if decision.alert else ''}",
                flush=True,
            )
            self._publish_fall_state(decision.label)

        return True

    def _publish_fall_state(self, label: str) -> None:
        """Publica fall_state no FIWARE só quando o valor canónico muda."""
        state = normalize_fall_state(label)
        if state == self._last_published_fall_state:
            return
        try:
            notify_fall(label)
            self._last_published_fall_state = state
        except Exception as error:
            print(f"Falha FIWARE notify_fall: {error}", flush=True)

    def run(self) -> None:
        while True:
            if not self.__consume_raw_frame():
                break

    def stop(self) -> None:
        try:
            self.raw_frame_queue.put_nowait(None)
        except queue.Full:
            try:
                self.raw_frame_queue.get_nowait()
            except queue.Empty:
                pass
            try:
                self.raw_frame_queue.put_nowait(None)
            except queue.Full:
                pass

    def insert_raw_frame(self, frame: np.ndarray, capture_date: float) -> None:
        try:
            self.raw_frame_queue.put_nowait((frame, capture_date))
        except queue.Full:
            try:
                self.raw_frame_queue.get_nowait()
            except queue.Empty:
                pass
            self.raw_frame_queue.put_nowait((frame, capture_date))


@lru_cache
def get_worker() -> FrameWorker:
    settings = get_settings()
    classifier_id = get_classifier_id()
    print(f"FrameWorker classifier={classifier_id}", flush=True)
    return FrameWorker(
        settings.frame_rate,
        create_classifier(classifier_id),
    )
