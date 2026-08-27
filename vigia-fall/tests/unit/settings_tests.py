"""Testes unitários para shared.models.settings."""

import pytest

from models import Settings, get_settings


def test_Settings_from_env_ComVariaveisDefinidas_RetornaConfiguracaoCorreta(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Arrange
    monkeypatch.setattr("shared.models.settings.load_dotenv", lambda: None)
    monkeypatch.setenv("CAPTURE_SOURCE", "2")
    monkeypatch.setenv("SHOW_VIDEO", "true")
    monkeypatch.setenv("YOLO_POSE_MODEL", "modelo-teste")
    monkeypatch.setenv("FRAME_RATE", "24")
    monkeypatch.setenv("SLIDER_WINDOW", "15")

    # Act
    settings = Settings.from_env()

    # Assert
    assert settings.capture_source == 2
    assert settings.show_video is True
    assert settings.yolo_pose_model == "modelo-teste"
    assert settings.frame_rate == 24
    assert settings.slider_window_size == 15


def test_Settings_from_env_SemVariaveisDefinidas_RetornaValoresPadrao(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Arrange
    monkeypatch.setattr("shared.models.settings.load_dotenv", lambda: None)
    monkeypatch.delenv("CAPTURE_SOURCE", raising=False)
    monkeypatch.delenv("SHOW_VIDEO", raising=False)
    monkeypatch.delenv("YOLO_POSE_MODEL", raising=False)
    monkeypatch.delenv("FRAME_RATE", raising=False)
    monkeypatch.delenv("SLIDER_WINDOW", raising=False)

    # Act
    settings = Settings.from_env()

    # Assert
    assert settings == Settings()


def test_get_settings_ChamadoDuasVezes_RetornaMesmaInstancia(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Arrange
    monkeypatch.setenv("FRAME_RATE", "10")

    # Act
    primeira = get_settings()
    segunda = get_settings()

    # Assert
    assert primeira is segunda
