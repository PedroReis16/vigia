"""Testes do MathFallClassifier."""

from __future__ import annotations

from unittest.mock import MagicMock

import numpy as np
import pytest

from core.classifiers.math_classifier import MathFallClassifier
from core.models.fall_detector import FallState
from core.models.types import PoseObservation


def _obs(person_id: int, ts: float, conf: float = 0.9) -> PoseObservation:
    kpts = np.zeros((17, 3), dtype=np.float32)
    kpts[5] = [10, 20, conf]
    kpts[6] = [30, 20, conf]
    kpts[11] = [12, 50, conf]
    kpts[12] = [28, 50, conf]
    return PoseObservation(person_id=person_id, keypoints=kpts, timestamp=ts)


def _passthrough_kalman(pid, ts, points):
    return {
        i: {"x": points[i][0], "y": points[i][1], "vx": 0, "vy": 0} for i in points
    }


def _patch_math(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "core.classifiers.math_classifier.apply_kalman", _passthrough_kalman
    )
    monkeypatch.setattr(
        "core.classifiers.math_classifier.get_smoothed_scale",
        lambda pid, raw: max(raw, 1.0),
    )
    monkeypatch.setattr(
        "core.classifiers.math_classifier.align_and_store_pca_angle",
        lambda pid, angle: angle,
    )


def test_math_classifier_janela_incompleta_sem_decisao(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_math(monkeypatch)
    clf = MathFallClassifier(window_size=3)
    assert clf.process([_obs(1, 1.0)]) == []
    assert clf.get_window_fill()[1] == (1, 3)


def test_math_classifier_janela_cheia_emite_decisao(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_math(monkeypatch)
    monkeypatch.setattr(
        "core.classifiers.math_classifier.extract_features",
        lambda window: {"trunk_angle_delta": 0.1},
    )
    monkeypatch.setattr(
        "core.classifiers.math_classifier.normalize_features",
        lambda features: features,
    )
    monkeypatch.setattr(
        "core.classifiers.math_classifier.compute_fall_score",
        lambda features, weights: 0.2,
    )

    detector = MagicMock()
    detector.update.return_value = FallState.NORMAL
    store = MagicMock()
    store.get_or_create.return_value = MagicMock(fall_detector=detector)
    monkeypatch.setattr(
        "core.classifiers.math_classifier.get_person_runtime_store",
        lambda: store,
    )

    clf = MathFallClassifier(window_size=2)
    assert clf.process([_obs(1, 1.0)]) == []
    decisions = clf.process([_obs(1, 2.0)])
    assert len(decisions) == 1
    assert decisions[0].label == "NORMAL"
    assert decisions[0].alert is False


def test_math_classifier_duas_pessoas_janelas_independentes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_math(monkeypatch)
    monkeypatch.setattr(
        "core.classifiers.math_classifier.extract_features",
        lambda window: {},
    )
    monkeypatch.setattr(
        "core.classifiers.math_classifier.normalize_features",
        lambda features: features,
    )
    monkeypatch.setattr(
        "core.classifiers.math_classifier.compute_fall_score",
        lambda features, weights: 0.1,
    )

    detector = MagicMock()
    detector.update.return_value = FallState.NORMAL
    store = MagicMock()
    store.get_or_create.return_value = MagicMock(fall_detector=detector)
    monkeypatch.setattr(
        "core.classifiers.math_classifier.get_person_runtime_store",
        lambda: store,
    )

    clf = MathFallClassifier(window_size=2)
    clf.process([_obs(1, 1.0), _obs(2, 1.0)])
    decisions = clf.process([_obs(1, 2.0), _obs(2, 2.0)])
    assert {d.person_id for d in decisions} == {1, 2}


def test_math_classifier_sem_juntas_nao_entra_janela(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_math(monkeypatch)
    kpts = np.zeros((17, 3), dtype=np.float32)
    kpts[0] = [1, 2, 0.9]
    obs = PoseObservation(person_id=1, keypoints=kpts, timestamp=1.0)
    clf = MathFallClassifier(window_size=1)
    assert clf.process([obs]) == []
    assert clf.get_window_fill() == {}


def test_math_classifier_transicao_fall_dispara_alert(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_math(monkeypatch)
    monkeypatch.setattr(
        "core.classifiers.math_classifier.extract_features",
        lambda window: {},
    )
    monkeypatch.setattr(
        "core.classifiers.math_classifier.normalize_features",
        lambda features: features,
    )
    monkeypatch.setattr(
        "core.classifiers.math_classifier.compute_fall_score",
        lambda features, weights: 0.9,
    )

    detector = MagicMock()
    detector.update.side_effect = [FallState.SUSPECT, FallState.FALL]
    store = MagicMock()
    store.get_or_create.return_value = MagicMock(fall_detector=detector)
    monkeypatch.setattr(
        "core.classifiers.math_classifier.get_person_runtime_store",
        lambda: store,
    )

    clf = MathFallClassifier(window_size=1)
    first = clf.process([_obs(1, 1.0)])
    second = clf.process([_obs(1, 2.0)])
    assert first[0].alert is False
    assert second[0].alert is True
    assert second[0].label == "FALL"
