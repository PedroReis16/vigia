import numpy as np

from core.models.types import PoseObservation
from core.point_filter import filter_observations
from vigia_lab.idpolicy import IdGrace
from vigia_lab.session import PoseFrame, TakeConfig, run_take


def test_grace_keeps_recently_seen_ids_and_expires_them() -> None:
    g = IdGrace(grace_s=1.5)
    assert g.active({1}, 0.0) == {1}
    assert g.active(set(), 1.0) == {1}          # sumiu 1,0 s: ainda ativo
    assert g.active({2}, 1.4) == {1, 2}
    assert g.active(set(), 1.6) == {2}          # 1 expirou (visto há 1,6 s)


class HistoryClassifier:
    """Guarda quantos frames cada pessoa acumulou; cleanup apaga como o vigia."""

    def __init__(self) -> None:
        self.frames: dict[int, int] = {}
        self.wiped: list[int] = []

    def process(self, obs):
        for o in obs:
            self.frames[o.person_id] = self.frames.get(o.person_id, 0) + 1
        return []

    def cleanup(self, ids):
        for pid in [p for p in self.frames if p not in ids]:
            self.wiped.append(pid)
            del self.frames[pid]


class Store:
    def cleanup(self, ids):
        pass


def _kp() -> np.ndarray:
    k = np.zeros((17, 3), dtype=np.float32)
    k[:, :2] = 60.0
    k[:, 2] = 0.9
    return k


def _frames(untracked_at: set[int], fps: float = 30.0, seconds: float = 6.0):
    for i in range(int(fps * seconds)):
        t = 1000.0 + i / fps
        if i in untracked_at:
            # tracker sem tracks: caixa crua, o vigia numera 0..n-1
            yield PoseFrame([PoseObservation(0, _kp(), t)], None, 20.0, t, t, untracked=True)
        else:
            yield PoseFrame([PoseObservation(1, _kp(), t)], None, 20.0, t, t)


def test_baseline_wipes_history_on_untracked_frame_but_grace_keeps_it() -> None:
    cfg = dict(duration_s=5.0, countdown_s=0.0, frame_rate=12)
    untracked = {60, 61, 62}                    # ~2 s: cobre pelo menos 1 frame entregue

    base = HistoryClassifier()
    run_take(_frames(untracked), TakeConfig(**cfg, ids_mode="baseline"), {"h": base},
             filter_observations, Store)
    assert 1 in base.wiped                       # pessoa 1 apagada (bug do vigia)

    fixed = HistoryClassifier()
    out = run_take(_frames(untracked), TakeConfig(**cfg, ids_mode="grace"), {"h": fixed},
                   filter_observations, Store)
    assert 1 not in fixed.wiped and 0 not in fixed.frames   # sem ID falso, sem apagar
    assert out.recorder.id_stats()["untracked_frames"] == 3
    assert out.recorder.id_stats()["id_set_changes_delivered"] == 0
