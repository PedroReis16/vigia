import numpy as np

from core.models.types import FallDecision, PoseObservation
from core.point_filter import filter_observations
from vigia_lab.delivery import deliver_batch


class Recorder:
    def __init__(self) -> None:
        self.calls: list[tuple] = []

    def process(self, obs):
        self.calls.append(("process", [o.person_id for o in obs]))
        return [FallDecision(o.person_id, "ADL", False) for o in obs]

    def cleanup(self, ids):
        self.calls.append(("cleanup", set(ids)))


class Store:
    def __init__(self, log: list) -> None:
        self.log = log

    def cleanup(self, ids):
        self.log.append(("store_cleanup", set(ids)))


def _obs(pid: int, torso: bool = True) -> PoseObservation:
    kp = np.zeros((17, 3), dtype=np.float32)
    if torso:
        kp[[5, 6, 11, 12]] = (10, 10, 0.9)
    else:
        kp[0] = (10, 10, 0.9)
    return PoseObservation(person_id=pid, keypoints=kp, timestamp=1.0)


def test_order_and_active_ids_come_from_raw_batch() -> None:
    rec = Recorder()
    store = Store(rec.calls)
    # pessoa 2 sem tronco: sai do filtro, mas continua em active_ids
    res = deliver_batch([_obs(1), _obs(2, torso=False)], {"m": rec}, filter_observations, lambda: store)
    assert rec.calls == [
        ("process", [1]),
        ("store_cleanup", {1, 2}),
        ("cleanup", {1, 2}),
    ]
    assert res.n_filtered == 1 and not res.reset_all


def test_empty_batch_is_delivered_and_flags_reset() -> None:
    rec = Recorder()
    res = deliver_batch([], {"m": rec}, filter_observations, lambda: Store(rec.calls))
    assert res.reset_all
    assert ("cleanup", set()) in rec.calls


def test_matches_frame_worker_handle(monkeypatch) -> None:
    import core.frame_worker as fw

    rec = Recorder()
    store = Store(rec.calls)
    monkeypatch.setattr(fw, "get_person_runtime_store", lambda: store)
    monkeypatch.setattr(fw, "enqueue_fall_state", lambda *a, **k: None)
    worker = fw.FrameWorker.__new__(fw.FrameWorker)
    batch = [_obs(1), _obs(2, torso=False)]
    worker._handle(batch, rec)
    expected = list(rec.calls)

    rec2 = Recorder()
    deliver_batch(batch, {"m": rec2}, filter_observations, lambda: Store(rec2.calls))
    assert rec2.calls == expected
