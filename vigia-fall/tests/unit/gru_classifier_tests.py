"""
Testes unitários para GRUFallClassifier.
Mocka onnxruntime.InferenceSession — não precisa do arquivo .onnx em disco.
"""

from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from capture.models.gru_classifier import GRUFallClassifier, ALERT_PREDS_FALL


def _fake_window(T: int = 20, all_valid: bool = True) -> np.ndarray:
    """Janela (T, 51) com keypoints plausíveis."""
    w = np.random.rand(T, 51).astype(np.float32)
    if all_valid:
        for j in [5, 6, 11, 12]:
            w[:, j * 3 + 2] = 0.8  # conf > 0 nos joints obrigatórios
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
    session.run.return_value = [None, np.array([[0.8, 0.2]])]

    result = clf.predict(_fake_window(), person_id=1)

    assert result is not None
    assert "label" in result
    assert "probs" in result
    assert "alert" in result
    assert "n_valid_frames" in result


def test_GRUFallClassifier_predict_ComJanelaInvalida_RetornaNone(classifier):
    clf, _ = classifier
    window = np.zeros((20, 51), dtype=np.float32)  # conf=0 em todos

    result = clf.predict(window, person_id=1)

    assert result is None


def test_GRUFallClassifier_predict_ComDuasQuedasConsecutivas_DisparaAlerta(classifier):
    clf, session = classifier
    session.run.return_value = [None, np.array([[0.1, 0.9]])]  # FALL

    clf.predict(_fake_window(), person_id=1)
    result = clf.predict(_fake_window(), person_id=1)

    assert result["alert"] is True
    assert result["label"] == "FALL"


def test_GRUFallClassifier_predict_ComUmaQuedaIsolada_NaoDisparaAlerta(classifier):
    clf, session = classifier
    session.run.side_effect = [
        [None, np.array([[0.8, 0.2]])],  # ADL
        [None, np.array([[0.1, 0.9]])],  # FALL
    ]

    clf.predict(_fake_window(), person_id=1)
    result = clf.predict(_fake_window(), person_id=1)

    assert result["alert"] is False


def test_GRUFallClassifier_predict_PessoasDiferentes_HistoricoIsolado(classifier):
    clf, session = classifier
    session.run.return_value = [None, np.array([[0.1, 0.9]])]  # FALL

    # pessoa 1: uma queda
    clf.predict(_fake_window(), person_id=1)
    # pessoa 2: uma queda isolada — histórico distinto
    result_p2 = clf.predict(_fake_window(), person_id=2)

    assert result_p2["alert"] is False


def test_GRUFallClassifier_normalize_window_ComJointsValidos_HipFicaOrigem(classifier):
    clf, _ = classifier
    window = _fake_window()

    normalized, n_valid = clf._normalize_window(window)

    assert normalized is not None
    assert n_valid > 0
    # hip médio (joints 11+12) deve estar em (0,0) após normalização
    hip_center = (normalized[:, 11 * 2 : 11 * 2 + 2] + normalized[:, 12 * 2 : 12 * 2 + 2]) / 2
    assert np.allclose(hip_center, 0, atol=0.1)


def test_GRUFallClassifier_normalize_window_ComJointConfiancaZero_MantemZero(classifier):
    clf, _ = classifier
    window = _fake_window()
    window[:, 0 * 3 + 2] = 0.0  # nariz (joint 0) com conf=0

    normalized, _ = clf._normalize_window(window)

    assert normalized is not None
    nose_xy = normalized[:, 0:2]
    assert np.all(nose_xy == 0)


def test_GRUFallClassifier_normalize_window_SemJointsValidos_RetornaNone(classifier):
    clf, _ = classifier
    window = np.zeros((20, 51), dtype=np.float32)

    normalized, n_valid = clf._normalize_window(window)

    assert normalized is None
    assert n_valid == 0
