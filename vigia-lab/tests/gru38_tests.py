import numpy as np

from core.models.types import PoseObservation
from vigia_lab import hud, models_gru, report
from vigia_lab.gru37 import Gru37Classifier


def _person(y_hip: float, t: float) -> PoseObservation:
    kp = np.zeros((17, 3), dtype=np.float32)
    kp[5] = (100, y_hip - 100, 0.9)
    kp[6] = (140, y_hip - 100, 0.9)
    kp[11] = (105, y_hip, 0.9)
    kp[12] = (135, y_hip, 0.9)
    return PoseObservation(person_id=1, keypoints=kp, timestamp=t)


def test_real_onnx_runs_with_the_gru37_contract() -> None:
    clf = Gru37Classifier(onnx_path=models_gru.GRU38_ONNX)
    decisions = []
    for i in range(40):
        t = i / 10.0
        decisions += clf.process([_person(200 + 6.0 * i, t)])
    assert decisions
    for d in decisions:
        probs = d.detail["probs"]
        assert len(probs) == 2 and abs(sum(probs) - 1.0) < 1e-5
        assert d.label == ("FALL" if probs[1] > probs[0] else "ADL")


def test_gru38_is_reported_and_locked() -> None:
    assert "gru38" in report.MODELS
    assert "gru38" in [key for key, _name in hud.MODEL_ORDER]
    assert "gru38_onnx" in models_gru.verify_lock()


def test_hud_cards_fit_in_the_window() -> None:
    last_bottom = 70 + (len(hud.MODEL_ORDER) - 1) * hud.CARD_STEP + hud.CARD_H
    assert last_bottom <= hud.H
    assert hud.CARD_H < hud.CARD_STEP
