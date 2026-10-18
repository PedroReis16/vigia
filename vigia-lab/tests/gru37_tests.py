from types import SimpleNamespace

import numpy as np
import pytest

from core.models.types import PoseObservation
from vigia_lab.gru37 import Gru37Classifier
from vigia_lab.pose_features import FEATURE_DIM


class FakeSession:
    """Registra as entradas; devolve prob. fixa."""

    def __init__(self, dim: int = FEATURE_DIM, fall: float = 0.1) -> None:
        self.dim = dim
        self.fall = fall
        self.inputs: list[np.ndarray] = []

    def get_inputs(self):
        return [SimpleNamespace(name="x", shape=["b", 20, self.dim])]

    def run(self, _outputs, feed):
        self.inputs.append(feed["x"])
        return [np.array([[1 - self.fall, self.fall]], dtype=np.float32)]


def _person(y_hip: float, t: float, pid: int = 1) -> PoseObservation:
    kp = np.zeros((17, 3), dtype=np.float32)
    kp[5] = (100, y_hip - 100, 0.9)
    kp[6] = (140, y_hip - 100, 0.9)
    kp[11] = (105, y_hip, 0.9)
    kp[12] = (135, y_hip, 0.9)
    return PoseObservation(person_id=pid, keypoints=kp, timestamp=t)


def _run_fall(fps: float, session: FakeSession, seconds: float = 4.0, speed_px_s: float = 60.0):
    clf = Gru37Classifier(session=session)
    out = []
    for i in range(int(seconds * fps)):
        t = i / fps
        out += clf.process([_person(200 + speed_px_s * t, t)])
    return out


def test_rejects_model_with_wrong_feature_dim() -> None:
    with pytest.raises(ValueError):
        Gru37Classifier(session=FakeSession(dim=34))


@pytest.mark.parametrize("fps", [8.0, 12.0, 22.0])
def test_velocity_scale_independent_of_input_fps(fps: float) -> None:
    ref = FakeSession()
    _run_fall(10.0, ref)
    s = FakeSession()
    _run_fall(fps, s)
    assert ref.inputs and s.inputs
    vy_ref = np.mean(ref.inputs[-1][0, 2:, 35])   # canal v_y (índice 35)
    vy = np.mean(s.inputs[-1][0, 2:, 35])
    assert vy_ref > 0
    assert vy == pytest.approx(vy_ref, rel=0.15)


def test_no_inference_before_two_seconds_of_history() -> None:
    s = FakeSession()
    _run_fall(10.0, s, seconds=1.5)
    assert s.inputs == []


def test_alert_needs_two_consecutive_fall_predictions() -> None:
    s = FakeSession(fall=0.9)
    decisions = _run_fall(10.0, s, seconds=4.0)
    alerts = [d.alert for d in decisions]
    assert alerts[0] is False and any(alerts[1:])


def test_cleanup_drops_person_state() -> None:
    clf = Gru37Classifier(session=FakeSession())
    clf.process([_person(200, 0.0, pid=7)])
    clf.cleanup(set())
    assert 7 not in clf._history
