"""
Worker para processamento assíncrono dos frames capturados
"""

from functools import lru_cache
import logging
import queue
import time

import numpy as np  # pyright: ignore[reportMissingImports]

from capture.classifiers import FallClassifier, create_classifier, get_classifier_id
from capture.classifiers.types import FallDecision
from capture.frame_processor import extract_poses
from integration.fall_shm import enqueue_fall_state
from integration.fiware_runner import normalize_fall_state
from shared import get_settings
from shared.log_bridge import emit_log

_PERIODIC_THROTTLE_S = 5.0
_QUEUE_MAXSIZE = 2


def _format_decision_message(decision: FallDecision) -> str:
    label_part = f"state Person {decision.person_id}: {decision.label}"
    if decision.alert:
        label_part += " ALERT"
    if decision.detail and "score" in decision.detail:
        score = decision.detail["score"]
        label_part += f" score={score:.2f}"
    return label_part


def _format_window_fill(classifier: FallClassifier) -> str:
    get_fill = getattr(classifier, "get_window_fill", None)
    capacity = getattr(classifier, "window_capacity", None)
    if get_fill is not None:
        fills = get_fill()
        if fills:
            parts = [
                f"p{person_id}={fill}/{max_size}"
                for person_id, (fill, max_size) in sorted(fills.items())
            ]
            return " ".join(parts)
    if capacity is not None:
        return f"window=0/{capacity}"
    return "window=0/?"


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
        self.raw_frame_queue = queue.Queue(maxsize=_QUEUE_MAXSIZE)
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
        self._last_yolo_ms = 0.0
        self._queue_skips = 0
        self._enqueues = 0
        self._processed_frames = 0
        self._metrics_window_start_ts: float | None = None
        self._frame_rate = frame_rate

    def can_accept_frame(self) -> bool:
        """True quando a fila está vazia (backpressure)."""
        return self.raw_frame_queue.empty()

    def __consume_raw_frame(self) -> bool:
        item = self.raw_frame_queue.get()

        if item is None:
            return False

        frame, capture_date = item

        started = time.perf_counter()
        observations = extract_poses(frame, capture_date)
        self._last_yolo_ms = (time.perf_counter() - started) * 1000.0
        self.raw_frame_queue.task_done()
        self._processed_frames += 1
        self._maybe_log_metrics(capture_date)

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

    def _maybe_log_metrics(self, capture_ts: float) -> None:
        if self._metrics_window_start_ts is None:
            self._metrics_window_start_ts = capture_ts
            return
        if not self._periodic_due("metrics", capture_ts, _PERIODIC_THROTTLE_S):
            return

        elapsed = capture_ts - self._metrics_window_start_ts
        if elapsed <= 0:
            return

        enqueue_fps = self._enqueues / elapsed
        window_fps = self._processed_frames / elapsed
        emit_log(
            logging.INFO,
            (
                f"capture metrics: yolo_ms={self._last_yolo_ms:.0f} "
                f"enqueue_fps={enqueue_fps:.1f} window_fps={window_fps:.1f} "
                f"queue_skips={self._queue_skips}"
            ),
            capture_ts=capture_ts,
        )
        self._metrics_window_start_ts = capture_ts
        self._enqueues = 0
        self._processed_frames = 0
        self._queue_skips = 0

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
        window_info = _format_window_fill(self._classifier)
        message = f"state warmup: poses={pose_count} {window_info} janela incompleta"
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

    def try_insert_raw_frame(self, frame: np.ndarray, capture_date: float) -> bool:
        """
        Enfileira frame se a fila estiver vazia.
        Retorna False quando há backpressure (skip, sem drop-oldest).
        """
        if not self.can_accept_frame():
            self._queue_skips += 1
            return False
        try:
            self.raw_frame_queue.put_nowait((frame, capture_date))
            self._enqueues += 1
            return True
        except queue.Full:
            self._queue_skips += 1
            return False

    def insert_raw_frame(self, frame: np.ndarray, capture_date: float) -> bool:
        """Alias de try_insert_raw_frame para compatibilidade com testes."""
        return self.try_insert_raw_frame(frame, capture_date)


@lru_cache
def get_worker() -> FrameWorker:
    settings = get_settings()
    classifier_id = get_classifier_id()
    emit_log(logging.INFO, f"state startup: FrameWorker classifier={classifier_id}")
    return FrameWorker(
        settings.frame_rate,
        create_classifier(classifier_id),
    )
