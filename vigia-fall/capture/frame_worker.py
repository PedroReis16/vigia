"""
Worker para processamento assíncrono dos frames capturados
"""

from functools import lru_cache
import logging
import queue

import numpy as np  # pyright: ignore[reportMissingImports]

from capture.classifiers import FallClassifier, create_classifier, get_classifier_id
from capture.classifiers.types import FallDecision
from capture.frame_processor import extract_poses
from integration.fall_shm import enqueue_fall_state
from integration.fiware_runner import normalize_fall_state
from shared import get_settings
from shared.log_bridge import emit_log

_PERIODIC_THROTTLE_S = 5.0


def _format_decision_message(decision: FallDecision) -> str:
    label_part = f"state Person {decision.person_id}: {decision.label}"
    if decision.alert:
        label_part += " ALERT"
    if decision.detail and "score" in decision.detail:
        score = decision.detail["score"]
        label_part += f" score={score:.2f}"
    return label_part


class FrameWorker:
    """
    Worker para processamento assíncrono dos frames capturados
    """

    def __init__(
        self,
        frame_rate: int,
        classifier: FallClassifier | None = None,
        *,
        state_log_mode: str | None = None,
        state_log_interval_s: float | None = None,
    ) -> None:
        settings = get_settings()
        self.raw_frame_queue = queue.Queue(maxsize=frame_rate)
        self._classifier = classifier if classifier is not None else create_classifier()
        self._last_published_fall_state: str | None = None
        self._last_logged: dict[int, str] = {}
        self._last_state_log_ts: dict[int, float] = {}
        self._last_periodic_log: dict[str, float] = {}
        self._state_log_mode = state_log_mode or settings.state_log_mode
        self._state_log_interval_s = (
            state_log_interval_s
            if state_log_interval_s is not None
            else settings.state_log_interval_s
        )

    def __consume_raw_frame(self) -> bool:
        item = self.raw_frame_queue.get()

        if item is None:
            return False

        frame, capture_date = item

        observations = extract_poses(frame, capture_date)
        self.raw_frame_queue.task_done()

        if not observations:
            self._log_no_person(capture_date)
            return True

        decisions = self._classifier.process(observations)
        if not decisions:
            self._log_warmup(len(observations), capture_date)

        for decision in decisions:
            self._log_decision(decision, capture_date)
            self._publish_fall_state(decision.label, capture_date)

        return True

    def _periodic_due(self, key: str, capture_ts: float, interval: float) -> bool:
        last = self._last_periodic_log.get(key, 0.0)
        if capture_ts - last >= interval:
            self._last_periodic_log[key] = capture_ts
            return True
        return False

    def _log_no_person(self, capture_ts: float) -> None:
        if self._state_log_mode == "verbose":
            emit_log(
                logging.INFO,
                "state no_person: frame ok, zero poses",
                capture_ts=capture_ts,
            )
            return
        if self._periodic_due("no_person", capture_ts, _PERIODIC_THROTTLE_S):
            emit_log(
                logging.INFO,
                "state no_person: frame ok, zero poses",
                capture_ts=capture_ts,
            )

    def _log_warmup(self, pose_count: int, capture_ts: float) -> None:
        message = f"state warmup: poses={pose_count} janela incompleta"
        if self._state_log_mode == "verbose":
            emit_log(logging.INFO, message, capture_ts=capture_ts)
            return
        if self._periodic_due("warmup", capture_ts, _PERIODIC_THROTTLE_S):
            emit_log(logging.INFO, message, capture_ts=capture_ts)

    def _log_decision(self, decision: FallDecision, capture_ts: float) -> None:
        person_id = decision.person_id
        label = decision.label
        message = _format_decision_message(decision)

        if self._state_log_mode == "verbose":
            emit_log(
                logging.INFO,
                message,
                capture_ts=capture_ts,
                person_id=person_id,
            )
            self._last_logged[person_id] = label
            self._last_state_log_ts[person_id] = capture_ts
            return

        changed = self._last_logged.get(person_id) != label
        heartbeat_due = (
            self._state_log_mode == "heartbeat"
            and capture_ts - self._last_state_log_ts.get(person_id, 0.0)
            >= self._state_log_interval_s
        )

        if changed or decision.alert or heartbeat_due:
            emit_log(
                logging.INFO,
                message,
                capture_ts=capture_ts,
                person_id=person_id,
            )
            if changed:
                self._last_logged[person_id] = label
            self._last_state_log_ts[person_id] = capture_ts

    def _publish_fall_state(self, label: str, capture_ts: float) -> None:
        """Enfileira fall_state para o processo FIWARE só quando o valor canónico muda."""
        state = normalize_fall_state(label)
        if state == self._last_published_fall_state:
            return
        try:
            enqueue_fall_state(label, capture_ts=capture_ts)
            self._last_published_fall_state = state
        except Exception as error:
            emit_log(
                logging.WARNING,
                f"Falha ao enfileirar fall_state: {error}",
                capture_ts=capture_ts,
            )

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
    emit_log(logging.INFO, f"state startup: FrameWorker classifier={classifier_id}")
    return FrameWorker(
        settings.frame_rate,
        create_classifier(classifier_id),
    )
