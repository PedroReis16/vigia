"""Testes da fila e do worker do core."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from core.frame_queue import FrameQueue
from core.frame_worker import FrameWorker, save_points
from core.models.types import FallDecision, PoseObservation
from core.point_filter import filter_observations


def _valid_kpts(conf: float = 0.9) -> np.ndarray:
    kpts = np.zeros((17, 3), dtype=np.float32)
    kpts[5] = [10, 20, conf]
    kpts[6] = [30, 20, conf]
    kpts[11] = [12, 50, conf]
    kpts[12] = [28, 50, conf]
    return kpts


def _obs(person_id: int = 1, ts: float = 1.0, conf: float = 0.9) -> PoseObservation:
    return PoseObservation(
        person_id=person_id, keypoints=_valid_kpts(conf), timestamp=ts
    )


def test_frame_queue_ThrottleEBackpressure():
    q = FrameQueue(frame_rate=1, maxsize=1)
    assert q.push([_obs(1)]) is True
    assert q.push([_obs(2)]) is False
    assert q.get(timeout=0.1)[0].person_id == 1


def test_save_points_EnfileiraLoteBruto(monkeypatch: pytest.MonkeyPatch):
    q = FrameQueue(frame_rate=1000, maxsize=2)
    monkeypatch.setattr("core.frame_worker.get_frame_queue", lambda: q)

    save_points([_obs(3)])
    batch = q.get(timeout=0.1)
    assert len(batch) == 1
    assert batch[0].person_id == 3


def test_filter_observations_SemJuntasObrigatorias_Exclui():
    bad = np.zeros((17, 3), dtype=np.float32)
    bad[0] = [1, 2, 0.9]
    obs = PoseObservation(person_id=1, keypoints=bad, timestamp=1.0)
    assert filter_observations([obs]) == []


def test_filter_observations_ConfBaixa_Exclui():
    assert filter_observations([_obs(conf=0.1)]) == []


def test_filter_observations_Valido_MantemId():
    filtered = filter_observations([_obs(7), _obs(8)])
    assert [o.person_id for o in filtered] == [7, 8]


def test_worker_handle_FiltraClassificaEPublica():
    clf = MagicMock()
    clf.process.return_value = [
        FallDecision(person_id=1, label="NORMAL", alert=False),
    ]
    published: list[tuple] = []

    def _enqueue(label, *, person_id=0, capture_ts=0.0):
        published.append((label, person_id, capture_ts))

    worker = FrameWorker.__new__(FrameWorker)
    with (
        patch("core.frame_worker.enqueue_fall_state", side_effect=_enqueue),
        patch(
            "core.frame_worker.get_person_runtime_store",
            return_value=MagicMock(),
        ),
    ):
        worker._handle([_obs(1, 4.0), _obs(2, 4.0)], clf)

    called = clf.process.call_args[0][0]
    assert [o.person_id for o in called] == [1, 2]
    clf.cleanup.assert_called_once()
    assert published == [("NORMAL", 1, 4.0)]


def test_worker_handle_LoteVazio_LimpaEstado():
    clf = MagicMock()
    clf.process.return_value = []
    store = MagicMock()

    worker = FrameWorker.__new__(FrameWorker)
    with (
        patch("core.frame_worker.enqueue_fall_state") as enqueue,
        patch("core.frame_worker.get_person_runtime_store", return_value=store),
    ):
        worker._handle([], clf)

    clf.process.assert_called_once_with([])
    store.cleanup.assert_called_once_with(set())
    enqueue.assert_not_called()
