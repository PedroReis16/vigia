"""Thread do core: consome points brutos, classifica e publica fall_state."""

from __future__ import annotations

import logging
import queue
import threading

from core.frame_queue import get_frame_queue
from core.models.person_runtime import get_person_runtime_store
from core.models.types import PoseObservation
from core.point_filter import filter_observations
from shared.fall_ipc import enqueue_fall_state

logger = logging.getLogger(__name__)

_worker: FrameWorker | None = None
_thread: threading.Thread | None = None


class FrameWorker:
    """Consome a FrameQueue na thread do core."""

    def __init__(self) -> None:
        self._queue = get_frame_queue()
        self._stop = threading.Event()

    def stop(self) -> None:
        self._stop.set()
        self._queue.put_sentinel()

    def run(self) -> None:
        from core.classifiers.factory import create_classifier

        classifier = create_classifier()
        logger.info("Core worker iniciado")

        while not self._stop.is_set():
            try:
                batch = self._queue.get(timeout=0.2)
            except queue.Empty:
                continue
            if batch is None:
                break
            self._handle(batch, classifier)

        logger.info("Core worker encerrado")

    def _handle(self, batch: list[PoseObservation], classifier) -> None:
        active_ids = {obs.person_id for obs in batch}
        filtered = filter_observations(batch)
        decisions = classifier.process(filtered)
        get_person_runtime_store().cleanup(active_ids)
        cleanup = getattr(classifier, "cleanup", None)
        if cleanup is not None:
            cleanup(active_ids)

        capture_ts = batch[0].timestamp if batch else 0.0
        for decision in decisions:
            enqueue_fall_state(
                decision.label,
                person_id=decision.person_id,
                capture_ts=capture_ts,
            )
            logger.info(
                "fall_state=%s person_id=%s alert=%s",
                decision.label,
                decision.person_id,
                decision.alert,
            )


def save_points(observations: list[PoseObservation]) -> None:
    """Enfileira points brutos. Não filtra nem classifica."""
    get_frame_queue().push(observations)


def start_core_worker() -> None:
    """Arranca a thread do core se ainda não estiver a correr."""
    global _worker, _thread
    if _thread is not None and _thread.is_alive():
        return
    _worker = FrameWorker()
    _thread = threading.Thread(target=_worker.run, name="core-worker", daemon=True)
    _thread.start()


def stop_core_worker() -> None:
    """Pede paragem e espera a thread do core."""
    global _worker, _thread
    if _worker is not None:
        _worker.stop()
    if _thread is not None:
        _thread.join(timeout=2.0)
    _worker = None
    _thread = None
