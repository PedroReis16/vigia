"""Testes unitários para capture.frame_processor.process_frame."""

from unittest.mock import MagicMock

import numpy as np
import pytest

from capture.frame_processor import process_frame
from capture.frame_worker import FrameWorker


def test_process_frame_ComDeteccoesVazias_NaoInsereJanelaDeslizante(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Arrange
    worker = FrameWorker(frame_rate=2, slider_window_size=2)
    insercoes: list[np.ndarray] = []

    def fake_insert(window: np.ndarray) -> None:
        insercoes.append(window)

    modelo = MagicMock()
    modelo.predict.return_value = []

    monkeypatch.setattr("capture.frame_processor.get_yolo_model", lambda: modelo)
    monkeypatch.setattr("capture.frame_processor.get_worker", lambda: worker)
    monkeypatch.setattr(worker, "insert_slider_window", fake_insert)
    frame = np.zeros((8, 8, 3), dtype=np.uint8)

    # Act
    process_frame(frame)

    # Assert
    modelo.predict.assert_called_once_with(frame, device="cpu", conf=0.75)
    assert insercoes == []


def test_process_frame_ComDeteccoesValidas_InsereJanelaDeslizante(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Arrange
    worker = FrameWorker(frame_rate=2, slider_window_size=2)
    insercoes: list[np.ndarray] = []

    def fake_insert(window: np.ndarray) -> None:
        insercoes.append(window)

    modelo = MagicMock()
    modelo.predict.return_value = [MagicMock()]

    monkeypatch.setattr("capture.frame_processor.get_yolo_model", lambda: modelo)
    monkeypatch.setattr("capture.frame_processor.get_worker", lambda: worker)
    monkeypatch.setattr(worker, "insert_slider_window", fake_insert)
    frame = np.zeros((8, 8, 3), dtype=np.uint8)

    # Act
    process_frame(frame)

    # Assert
    assert len(insercoes) == 1
    assert np.array_equal(insercoes[0], frame)


def test_process_frame_ComExcecaoNoModelo_NaoPropagaErro(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    # Arrange
    worker = FrameWorker(frame_rate=2, slider_window_size=2)
    insercoes: list[np.ndarray] = []

    def fake_insert(window: np.ndarray) -> None:
        insercoes.append(window)

    modelo = MagicMock()
    modelo.predict.side_effect = RuntimeError("falha no yolo")

    monkeypatch.setattr("capture.frame_processor.get_yolo_model", lambda: modelo)
    monkeypatch.setattr("capture.frame_processor.get_worker", lambda: worker)
    monkeypatch.setattr(worker, "insert_slider_window", fake_insert)

    # Act
    process_frame(np.zeros((8, 8, 3), dtype=np.uint8))

    # Assert
    assert insercoes == []
    captured = capsys.readouterr()
    assert "Erro ao processar o frame: falha no yolo" in captured.out
