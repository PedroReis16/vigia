"""Testes de leitura de classifier.json e factory."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from capture.classifiers.config import get_classifier_id
from capture.classifiers.factory import create_classifier
from capture.classifiers.gru_classifier import GruFallClassifier
from capture.classifiers.math_classifier import MathFallClassifier
from shared import get_settings


@pytest.fixture(autouse=True)
def _data_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    get_settings.cache_clear()
    return tmp_path


def test_get_classifier_id_sem_ficheiro_retorna_math() -> None:
    assert get_classifier_id() == "math"


def test_get_classifier_id_com_gru(tmp_path: Path) -> None:
    (tmp_path / "classifier.json").write_text(json.dumps({"classifier": "gru"}))
    assert get_classifier_id() == "gru"


def test_get_classifier_id_invalido_retorna_math(tmp_path: Path) -> None:
    (tmp_path / "classifier.json").write_text(json.dumps({"classifier": "svm"}))
    assert get_classifier_id() == "math"


def test_create_classifier_math() -> None:
    clf = create_classifier("math")
    assert isinstance(clf, MathFallClassifier)


def test_create_classifier_gru(monkeypatch: pytest.MonkeyPatch) -> None:
    from unittest.mock import MagicMock, patch

    with patch("capture.models.gru_classifier.ort.InferenceSession") as mock_ort:
        mock_session = MagicMock()
        mock_session.get_inputs.return_value = [MagicMock(name="input")]
        mock_ort.return_value = mock_session
        clf = create_classifier("gru")
        assert isinstance(clf, GruFallClassifier)
