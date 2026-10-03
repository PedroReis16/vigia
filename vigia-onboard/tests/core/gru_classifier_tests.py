"""Testes do GRU (ONNX mockado) e da strategy."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from core.classifiers.gru_classifier import (
    GRU_INTERVAL,
    GRU_WINDOW_SIZE,
    GruFallClassifier,
)
from core.models.gru_classifier import GRUFallClassifier
from core.models.types import PoseObservation


def _obs(person_id: int, ts: float) -> PoseObservation:
    kpts = np.ones((17, 3), dtype=np.float32) * 0.5
    kpts[:, 2] = 0.9
    kpts[5] = [10, 20, 0.9]
    kpts[6] = [30, 20, 0.9]
    kpts[11] = [12, 50, 0.9]
    kpts[12] = [28, 50, 0.9]
    return PoseObservation(person_id=person_id, keypoints=kpts, timestamp=ts)


def _fake_window(t_len: int = 20, all_valid: bool = True) -> np.ndarray:
    w = np.random.rand(t_len, 51).astype(np.float32)
    if all_valid:
        for j in [5, 6, 11, 12]:
            w[:, j * 3 + 2] = 0.8
    return w


@pytest.fixture
def gru_strategy():
    with patch("core.classifiers.gru_classifier.GRUFallClassifier") as mock_cls:
        model = MagicMock()
        mock_cls.return_value = model
        yield GruFallClassifier(), model


def test_gru_strategy_espera_janela_cheia(gru_strategy):
    strategy, model = gru_strategy
    for i in range(GRU_WINDOW_SIZE - 1):
        assert strategy.process([_obs(1, float(i))]) == []
        assert strategy.get_window_fill()[1] == (i + 1, GRU_WINDOW_SIZE)
    model.predict.assert_not_called()


def test_gru_strategy_infere_quando_pronto_e_respeita_intervalo(gru_strategy):
    strategy, model = gru_strategy
    model.predict.return_value = {
        "label": "ADL",
        "probs": [0.9, 0.1],
        "alert": False,
        "n_valid_frames": 20,
    }

    ts = 0.0
    decisions = []
    for _ in range(GRU_WINDOW_SIZE):
        decisions = strategy.process([_obs(1, ts)])
        ts += 0.01

    assert len(decisions) == 1
    assert decisions[0].label == "ADL"
    model.predict.assert_called_once()

    model.predict.reset_mock()
    assert strategy.process([_obs(1, ts)]) == []
    model.predict.assert_not_called()

    model.predict.return_value = {
        "label": "FALL",
        "probs": [0.1, 0.9],
        "alert": True,
        "n_valid_frames": 20,
    }
    decisions = strategy.process([_obs(1, ts + GRU_INTERVAL)])
    assert len(decisions) == 1
    assert decisions[0].alert is True


def test_gru_strategy_cleanup_remove_id(gru_strategy):
    strategy, _ = gru_strategy
    strategy.process([_obs(1, 0.0)])
    strategy.cleanup({2})
    assert strategy.get_window_fill() == {}


@pytest.fixture
def onnx_classifier():
    with patch("core.models.gru_classifier.ort.InferenceSession") as mock_cls:
        mock_session = MagicMock()
        mock_session.get_inputs.return_value = [MagicMock(name="input")]
        mock_cls.return_value = mock_session
        yield GRUFallClassifier(), mock_session


def test_GRUFallClassifier_predict_ComJanelaValida_RetornaDicionario(onnx_classifier):
    clf, session = onnx_classifier
    session.run.return_value = [np.array([[0.8, 0.2]])]
    result = clf.predict(_fake_window(), person_id=1)
    assert result is not None
    assert result["label"] == "ADL"


def test_GRUFallClassifier_predict_ComJanelaInvalida_RetornaNone(onnx_classifier):
    clf, _ = onnx_classifier
    assert clf.predict(np.zeros((20, 51), dtype=np.float32), person_id=1) is None


def test_GRUFallClassifier_predict_ComDuasQuedasConsecutivas_DisparaAlerta(
    onnx_classifier,
):
    clf, session = onnx_classifier
    session.run.return_value = [np.array([[0.1, 0.9]])]
    clf.predict(_fake_window(), person_id=1)
    result = clf.predict(_fake_window(), person_id=1)
    assert result["alert"] is True
    assert result["label"] == "FALL"
