"""Factory do classificador: classifier.json e fallback CLASSIFIER."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from core.classifiers.factory import create_classifier, read_classifier_id
from core.classifiers.math_classifier import MathFallClassifier
from shared import settings as st


@pytest.fixture(autouse=True)
def _clear_settings():
    st.get_settings.cache_clear()
    yield
    st.get_settings.cache_clear()


def test_factory_default_math(monkeypatch: pytest.MonkeyPatch, tmp_path):
    monkeypatch.setattr(st, "_load_onboard_env", lambda: None)
    monkeypatch.delenv("CLASSIFIER", raising=False)
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.setenv("SLIDER_WINDOW", "4")
    st.get_settings.cache_clear()
    clf = create_classifier()
    assert isinstance(clf, MathFallClassifier)
    assert clf.window_capacity == 4


def test_factory_json_vence_ambiente(monkeypatch: pytest.MonkeyPatch, tmp_path):
    monkeypatch.setattr(st, "_load_onboard_env", lambda: None)
    monkeypatch.setenv("CLASSIFIER", "math")
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    st.get_settings.cache_clear()
    (tmp_path / "classifier.json").write_text(
        json.dumps({"classifier": "gru"}), encoding="utf-8"
    )
    assert read_classifier_id() == "gru"


def test_factory_sem_ficheiro_usa_env(monkeypatch: pytest.MonkeyPatch, tmp_path):
    monkeypatch.setattr(st, "_load_onboard_env", lambda: None)
    monkeypatch.setenv("CLASSIFIER", "gru")
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    st.get_settings.cache_clear()
    assert read_classifier_id() == "gru"


def test_factory_gru_via_arg():
    with patch("core.classifiers.factory.GruFallClassifier") as gru_cls:
        gru_cls.return_value = MagicMock()
        clf = create_classifier("gru")
    gru_cls.assert_called_once()
    assert clf is gru_cls.return_value
