"""Testes de persistência do classificador (classifier.json)."""

from __future__ import annotations

import json

from provision import classifier, settings


def _clear_settings(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    settings.get_settings.cache_clear()


def test_get_classifier_default_sem_ficheiro(tmp_path, monkeypatch) -> None:
    _clear_settings(monkeypatch, tmp_path)
    assert classifier.get_classifier() == "math"
    assert not settings.get_classifier_path().exists()


def test_set_e_get_classifier_persiste(tmp_path, monkeypatch) -> None:
    _clear_settings(monkeypatch, tmp_path)
    classifier.set_classifier("gru")
    path = settings.get_classifier_path()
    assert path.exists()
    data = json.loads(path.read_text())
    assert data == {"classifier": "gru"}
    assert classifier.get_classifier() == "gru"


def test_get_classifier_invalido_retorna_math(tmp_path, monkeypatch) -> None:
    _clear_settings(monkeypatch, tmp_path)
    path = settings.get_classifier_path()
    path.write_text(json.dumps({"classifier": "onnx"}))
    assert classifier.get_classifier() == "math"
    path.write_text("not-json")
    assert classifier.get_classifier() == "math"


def test_ensure_materializa_default(tmp_path, monkeypatch) -> None:
    _clear_settings(monkeypatch, tmp_path)
    assert classifier.ensure_classifier_config() == "math"
    path = settings.get_classifier_path()
    assert path.exists()
    assert json.loads(path.read_text()) == {"classifier": "math"}


def test_ensure_reescreve_invalido(tmp_path, monkeypatch) -> None:
    _clear_settings(monkeypatch, tmp_path)
    path = settings.get_classifier_path()
    path.write_text(json.dumps({"classifier": "bad"}))
    assert classifier.ensure_classifier_config() == "math"
    assert json.loads(path.read_text()) == {"classifier": "math"}


def test_ensure_preserva_gru_valido(tmp_path, monkeypatch) -> None:
    _clear_settings(monkeypatch, tmp_path)
    classifier.set_classifier("gru")
    assert classifier.ensure_classifier_config() == "gru"
    assert json.loads(settings.get_classifier_path().read_text()) == {
        "classifier": "gru"
    }


def test_classifier_label_lcd() -> None:
    assert classifier.classifier_label("math") == "Matematico"
    assert classifier.classifier_label("gru") == "GRU"


def test_next_classifier_alterna() -> None:
    assert classifier.next_classifier("math") == "gru"
    assert classifier.next_classifier("gru") == "math"
