"""Testes unitários para capture.frame_worker.FrameWorker."""

import queue
import threading

import numpy as np
import pytest

from capture.frame_worker import FrameWorker, get_worker


def _frame() -> np.ndarray:
    return np.zeros((4, 4, 3), dtype=np.uint8)


def test_FrameWorker_insert_raw_frame_ComFilaDisponivel_ArmazenaFrame() -> None:
    # Arrange
    worker = FrameWorker(frame_rate=2, slider_window_size=2)
    frame = _frame()

    # Act
    worker.insert_raw_frame(frame)

    # Assert
    assert worker.raw_frame_queue.qsize() == 1
    assert np.array_equal(worker.raw_frame_queue.queue[0], frame)


def test_FrameWorker_insert_raw_frame_ComFilaCheia_SubstituiFrameMaisAntigo() -> None:
    # Arrange
    worker = FrameWorker(frame_rate=1, slider_window_size=2)
    frame_antigo = _frame()
    frame_novo = np.ones((4, 4, 3), dtype=np.uint8)
    worker.insert_raw_frame(frame_antigo)

    # Act
    worker.insert_raw_frame(frame_novo)

    # Assert
    assert worker.raw_frame_queue.qsize() == 1
    assert np.array_equal(worker.raw_frame_queue.queue[0], frame_novo)


def test_FrameWorker_insert_slider_window_ComFilaDisponivel_ArmazenaJanela() -> None:
    # Arrange
    worker = FrameWorker(frame_rate=2, slider_window_size=2)
    window = _frame()

    # Act
    worker.insert_slider_window(window)

    # Assert
    assert worker.slider_window_queue.qsize() == 1
    assert np.array_equal(worker.slider_window_queue.queue[0], window)


def test_FrameWorker_insert_slider_window_ComFilaCheia_SubstituiJanelaMaisAntiga() -> None:
    # Arrange
    worker = FrameWorker(frame_rate=2, slider_window_size=1)
    janela_antiga = _frame()
    janela_nova = np.ones((4, 4, 3), dtype=np.uint8)
    worker.insert_slider_window(janela_antiga)

    # Act
    worker.insert_slider_window(janela_nova)

    # Assert
    assert worker.slider_window_queue.qsize() == 1
    assert np.array_equal(worker.slider_window_queue.queue[0], janela_nova)


def test_FrameWorker_stop_ComWorkerAtivo_EncerraExecucaoRun(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Arrange
    processados: list[np.ndarray] = []

    def fake_process_frame(frame: np.ndarray) -> None:
        processados.append(frame)

    monkeypatch.setattr("capture.frame_processor.process_frame", fake_process_frame)
    worker = FrameWorker(frame_rate=2, slider_window_size=1)
    thread = threading.Thread(target=worker.run, daemon=True)
    thread.start()

    # Act
    worker.insert_raw_frame(_frame())
    worker.stop()
    thread.join(timeout=2)

    # Assert
    assert thread.is_alive() is False
    assert len(processados) == 1


def test_FrameWorker_run_ComSentinelNaFilaInicial_EncerraSemProcessar(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Arrange
    processados: list[np.ndarray] = []

    def fake_process_frame(frame: np.ndarray) -> None:
        processados.append(frame)

    monkeypatch.setattr("capture.frame_processor.process_frame", fake_process_frame)
    worker = FrameWorker(frame_rate=2, slider_window_size=2)
    worker.raw_frame_queue.put_nowait(None)
    thread = threading.Thread(target=worker.run, daemon=True)

    # Act
    thread.start()
    thread.join(timeout=2)

    # Assert
    assert thread.is_alive() is False
    assert processados == []


def test_get_worker_ComSettingsPadrao_RetornaWorkerConfigurado(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Arrange
    monkeypatch.setenv("FRAME_RATE", "5")
    monkeypatch.setenv("SLIDER_WINDOW", "7")

    # Act
    worker = get_worker()

    # Assert
    assert worker.raw_frame_queue.maxsize == 5
    assert worker.slider_window_queue.maxsize == 7


def test_FrameWorker_stop_ComFilasComEspaco_InsereSentinel() -> None:
    # Arrange
    worker = FrameWorker(frame_rate=2, slider_window_size=2)

    # Act
    worker.stop()

    # Assert
    assert worker.raw_frame_queue.get_nowait() is None
    assert worker.slider_window_queue.get_nowait() is None


def test_FrameWorker_stop_ComFilasCheias_LevantaQueueFull() -> None:
    # Arrange
    worker = FrameWorker(frame_rate=1, slider_window_size=1)
    worker.insert_raw_frame(_frame())
    worker.insert_slider_window(_frame())

    # Act / Assert
    with pytest.raises(queue.Full):
        worker.stop()
