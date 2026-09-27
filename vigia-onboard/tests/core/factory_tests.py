"""Factory do classificador via env CLASSIFIER."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from core.classifiers.factory import create_classifier
from core.classifiers.math_classifier import MathFallClassifier
from shared import settings as st


@pytest.fixture(autouse=True)
def _clear_settings():
    st.get_settings.cache_clear()
    yield
    st.get_settings.cache_clear()


def test_factory_default_math(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(st, "_load_onboard_env", lambda: None)
    monkeypatch.delenv("CLASSIFIER", raising=False)
    monkeypatch.setenv("SLIDER_WINDOW", "4")
    clf = create_classifier()
    assert isinstance(clf, MathFallClassifier)
    assert clf.window_capacity == 4


def test_factory_gru_via_arg():
    with patch("core.classifiers.factory.GruFallClassifier") as gru_cls:
        gru_cls.return_value = MagicMock()
        clf = create_classifier("gru")
    gru_cls.assert_called_once()
    assert clf is gru_cls.return_value
