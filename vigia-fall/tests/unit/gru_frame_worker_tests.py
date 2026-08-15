"""
Testes unitários para FrameWorker com pipeline GRU.
Mocka GRUFallClassifier e notify_fall para testes isolados.
"""

from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from capture.frame_worker import FrameWorker, GRU_WINDOW_SIZE


def _fake_raw_kpts() -> np.ndarray:
    return np.random.rand(51).astype(np.float32)


def _fake_frame_result(person_id: int = 1, timestamp: float = 0.0) -> dict:
    return {person_id: {"raw_kpts": _fake_raw_kpts(), "timestamp": timestamp}}


@pytest.fixture
def worker(monkeypatch):
    """FrameWorker com GRUFallClassifier mockado (sem arquivo ONNX)."""
    with patch("capture.frame_worker.GRUFallClassifier") as mock_cls:
        mock_clf = MagicMock()
        mock_clf.predict.return_value = None
        mock_cls.return_value = mock_clf
        w = FrameWorker(frame_rate=30, slider_window_size=20)
        yield w


def test_FrameWorker_GRU_ComJanelaIncompleta_NaoClassifica(monkeypatch, worker):
    """Com menos de GRU_WINDOW_SIZE frames, predict não deve ser chamado."""
    monkeypatch.setattr(
        "capture.frame_worker.process_frame",
        lambda f, d: _fake_frame_result(timestamp=d),
    )

    worker.raw_frame_queue.put_nowait((np.zeros((4, 4, 3), np.uint8), 0.0))
    worker.raw_frame_queue.put_nowait((None, 0.0))
    worker.run()

    worker._gru_classifier.predict.assert_not_called()


def test_FrameWorker_GRU_ComJanelaCheia_ChamaClassificador(monkeypatch, worker):
    """Com GRU_WINDOW_SIZE frames e intervalo suficiente, predict deve ser chamado."""
    call_count = 0

    def fake_process(frame, date):
        return {1: {"raw_kpts": _fake_raw_kpts(), "timestamp": date}}

    monkeypatch.setattr("capture.frame_worker.process_frame", fake_process)

    # Pré-enche o buffer com frames suficientes
    for _ in range(GRU_WINDOW_SIZE):
        worker._gru_buffers[1].append(_fake_raw_kpts())

    # Força último inference no passado para garantir elapsed >= GRU_INTERVAL
    worker._gru_last_inference[1] = 0.0

    worker.raw_frame_queue.put_nowait((np.zeros((4, 4, 3), np.uint8), 1.0))
    worker.raw_frame_queue.put_nowait((None, 0.0))
    worker.run()

    worker._gru_classifier.predict.assert_called_once()


def test_FrameWorker_GRU_ComAlerta_ChamaNotifyFall(monkeypatch):
    """Quando predict retorna alert=True, notify_fall deve ser chamado."""
    with patch("capture.frame_worker.GRUFallClassifier") as mock_cls:
        mock_clf = MagicMock()
        mock_clf.predict.return_value = {
            "label": "FALL",
            "probs": [0.1, 0.9],
            "alert": True,
            "n_valid_frames": 20,
        }
        mock_cls.return_value = mock_clf

        notificacoes = []
        monkeypatch.setattr(
            "capture.frame_worker.notify_fall",
            lambda label: notificacoes.append(label),
        )
        monkeypatch.setattr(
            "capture.frame_worker.process_frame",
            lambda f, d: {1: {"raw_kpts": _fake_raw_kpts(), "timestamp": d}},
        )

        w = FrameWorker(frame_rate=30, slider_window_size=20)
        for _ in range(GRU_WINDOW_SIZE):
            w._gru_buffers[1].append(_fake_raw_kpts())
        w._gru_last_inference[1] = 0.0

        w.raw_frame_queue.put_nowait((np.zeros((4, 4, 3), np.uint8), 1.0))
        w.raw_frame_queue.put_nowait((None, 0.0))
        w.run()

    assert "FALL" in notificacoes


def test_FrameWorker_GRU_SemAlerta_NaoChamaNotifyFall(monkeypatch):
    """Quando predict retorna alert=False, notify_fall não deve ser chamado."""
    with patch("capture.frame_worker.GRUFallClassifier") as mock_cls:
        mock_clf = MagicMock()
        mock_clf.predict.return_value = {
            "label": "ADL",
            "probs": [0.9, 0.1],
            "alert": False,
            "n_valid_frames": 20,
        }
        mock_cls.return_value = mock_clf

        notificacoes = []
        monkeypatch.setattr(
            "capture.frame_worker.notify_fall",
            lambda label: notificacoes.append(label),
        )
        monkeypatch.setattr(
            "capture.frame_worker.process_frame",
            lambda f, d: {1: {"raw_kpts": _fake_raw_kpts(), "timestamp": d}},
        )

        w = FrameWorker(frame_rate=30, slider_window_size=20)
        for _ in range(GRU_WINDOW_SIZE):
            w._gru_buffers[1].append(_fake_raw_kpts())
        w._gru_last_inference[1] = 0.0

        w.raw_frame_queue.put_nowait((np.zeros((4, 4, 3), np.uint8), 1.0))
        w.raw_frame_queue.put_nowait((None, 0.0))
        w.run()

    assert notificacoes == []


def test_FrameWorker_GRU_FalhaFIWARE_NaoPropagaExcecao(monkeypatch):
    """Falha em notify_fall não deve derrubar o worker."""
    with patch("capture.frame_worker.GRUFallClassifier") as mock_cls:
        mock_clf = MagicMock()
        mock_clf.predict.return_value = {
            "label": "FALL",
            "probs": [0.1, 0.9],
            "alert": True,
            "n_valid_frames": 20,
        }
        mock_cls.return_value = mock_clf

        monkeypatch.setattr(
            "capture.frame_worker.notify_fall",
            lambda label: (_ for _ in ()).throw(ConnectionError("broker offline")),
        )
        monkeypatch.setattr(
            "capture.frame_worker.process_frame",
            lambda f, d: {1: {"raw_kpts": _fake_raw_kpts(), "timestamp": d}},
        )

        w = FrameWorker(frame_rate=30, slider_window_size=20)
        for _ in range(GRU_WINDOW_SIZE):
            w._gru_buffers[1].append(_fake_raw_kpts())
        w._gru_last_inference[1] = 0.0

        w.raw_frame_queue.put_nowait((np.zeros((4, 4, 3), np.uint8), 1.0))
        w.raw_frame_queue.put_nowait((None, 0.0))

        # Não deve lançar exceção
        w.run()
