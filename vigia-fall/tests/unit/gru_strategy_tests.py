"""Testes do GruFallClassifier (strategy + buffer/intervalo)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from capture.classifiers.gru_classifier import (
    GRU_INTERVAL,
    GRU_WINDOW_SIZE,
    GruFallClassifier,
)
from capture.classifiers.types import PoseObservation


def _obs(person_id: int, ts: float) -> PoseObservation:
    kpts = np.ones((17, 3), dtype=np.float32) * 0.5
    kpts[:, 2] = 0.9
    kpts[5] = [10, 20, 0.9]
    kpts[6] = [30, 20, 0.9]
    kpts[11] = [12, 50, 0.9]
    kpts[12] = [28, 50, 0.9]
    return PoseObservation(person_id=person_id, keypoints=kpts, timestamp=ts)


@pytest.fixture
def gru_strategy():
    with patch("capture.classifiers.gru_classifier.GRUFallClassifier") as mock_cls:
        model = MagicMock()
        mock_cls.return_value = model
        strategy = GruFallClassifier()
        yield strategy, model


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
    for i in range(GRU_WINDOW_SIZE):
        decisions = strategy.process([_obs(1, ts)])
        ts += 0.01

    assert len(decisions) == 1
    assert decisions[0].label == "ADL"
    model.predict.assert_called_once()

    # Dentro do intervalo — sem nova inferência
    model.predict.reset_mock()
    assert strategy.process([_obs(1, ts)]) == []
    model.predict.assert_not_called()

    # Após intervalo
    model.predict.return_value = {
        "label": "FALL",
        "probs": [0.1, 0.9],
        "alert": True,
        "n_valid_frames": 20,
    }
    decisions = strategy.process([_obs(1, ts + GRU_INTERVAL)])
    assert len(decisions) == 1
    assert decisions[0].alert is True
