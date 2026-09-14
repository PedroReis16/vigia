"""Testes unitários para GRUFallClassifier (ONNX mockado)."""

from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from capture.models.gru_classifier import GRUFallClassifier


def _fake_window(t_len: int = 20, all_valid: bool = True) -> np.ndarray:
    w = np.random.rand(t_len, 51).astype(np.float32)
    if all_valid:
        for j in [5, 6, 11, 12]:
            w[:, j * 3 + 2] = 0.8
    return w


@pytest.fixture
def classifier():
    with patch("capture.models.gru_classifier.ort.InferenceSession") as mock_cls:
        mock_session = MagicMock()
        mock_session.get_inputs.return_value = [MagicMock(name="input")]
        mock_cls.return_value = mock_session
        clf = GRUFallClassifier()
        yield clf, mock_session


def test_GRUFallClassifier_predict_ComJanelaValida_RetornaDicionario(classifier):
    clf, session = classifier
    session.run.return_value = [np.array([[0.8, 0.2]])]

    result = clf.predict(_fake_window(), person_id=1)

    assert result is not None
    assert "label" in result
    assert "alert" in result


def test_GRUFallClassifier_predict_ComJanelaInvalida_RetornaNone(classifier):
    clf, _ = classifier
    window = np.zeros((20, 51), dtype=np.float32)

    assert clf.predict(window, person_id=1) is None


def test_GRUFallClassifier_predict_ComDuasQuedasConsecutivas_DisparaAlerta(classifier):
    clf, session = classifier
    session.run.return_value = [np.array([[0.1, 0.9]])]

    clf.predict(_fake_window(), person_id=1)
    result = clf.predict(_fake_window(), person_id=1)

    assert result["alert"] is True
    assert result["label"] == "FALL"


def test_GRUFallClassifier_predict_ComUmaQuedaIsolada_NaoDisparaAlerta(classifier):
    clf, session = classifier
    session.run.side_effect = [
        [np.array([[0.8, 0.2]])],
        [np.array([[0.1, 0.9]])],
    ]

    clf.predict(_fake_window(), person_id=1)
    result = clf.predict(_fake_window(), person_id=1)

    assert result["alert"] is False
