"""Testes unitários para capture.frame_worker.FrameWorker."""

from __future__ import annotations

import threading
from unittest.mock import MagicMock

import numpy as np
import pytest

from capture.classifiers.types import FallDecision
from capture.frame_worker import FrameWorker, get_worker
from shared import get_settings


def _frame() -> np.ndarray:
    return np.zeros((4, 4, 3), dtype=np.uint8)


def _mock_classifier() -> MagicMock:
    clf = MagicMock()
    clf.process.return_value = []
    return clf


def test_FrameWorker_insert_raw_frame_ComFilaDisponivel_ArmazenaFrame() -> None:
    worker = FrameWorker(frame_rate=2, classifier=_mock_classifier())
    frame = _frame()

    worker.insert_raw_frame(frame, 1.0)

    assert worker.raw_frame_queue.qsize() == 1
    queued_frame, ts = worker.raw_frame_queue.queue[0]
    assert np.array_equal(queued_frame, frame)
    assert ts == 1.0


def test_FrameWorker_insert_raw_frame_ComFilaCheia_SubstituiFrameMaisAntigo() -> None:
    worker = FrameWorker(frame_rate=1, classifier=_mock_classifier())
    frame_antigo = _frame()
    frame_novo = np.ones((4, 4, 3), dtype=np.uint8)
    worker.insert_raw_frame(frame_antigo, 1.0)

    worker.insert_raw_frame(frame_novo, 2.0)

    assert worker.raw_frame_queue.qsize() == 1
    queued_frame, ts = worker.raw_frame_queue.queue[0]
    assert np.array_equal(queued_frame, frame_novo)
    assert ts == 2.0


def test_FrameWorker_stop_ComWorkerAtivo_EncerraExecucaoRun(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    processados: list = []

    def fake_extract(frame, capture_date):
        processados.append(frame)
        return []

    monkeypatch.setattr("capture.frame_worker.extract_poses", fake_extract)
    worker = FrameWorker(frame_rate=2, classifier=_mock_classifier())
    thread = threading.Thread(target=worker.run, daemon=True)
    thread.start()

    worker.insert_raw_frame(_frame(), 1.0)
    worker.stop()
    thread.join(timeout=2)

    assert thread.is_alive() is False
    assert len(processados) == 1


def test_FrameWorker_run_ComSentinelNaFilaInicial_EncerraSemProcessar(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    processados: list = []

    def fake_extract(frame, capture_date):
        processados.append(frame)
        return []

    monkeypatch.setattr("capture.frame_worker.extract_poses", fake_extract)
    worker = FrameWorker(frame_rate=2, classifier=_mock_classifier())
    worker.raw_frame_queue.put_nowait(None)
    thread = threading.Thread(target=worker.run, daemon=True)

    thread.start()
    thread.join(timeout=2)

    assert thread.is_alive() is False
    assert processados == []


def test_FrameWorker_publica_todos_os_estados_com_dedupe(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    notified: list[str] = []

    def fake_extract(frame, capture_date):
        return [MagicMock()]

    clf = MagicMock()
    clf.process.return_value = [
        FallDecision(person_id=1, label="NORMAL", alert=False),
        FallDecision(person_id=1, label="SUSPECT", alert=False),
        FallDecision(person_id=1, label="FALL", alert=True),
        FallDecision(person_id=1, label="FALL", alert=True),
    ]
    monkeypatch.setattr("capture.frame_worker.extract_poses", fake_extract)
    monkeypatch.setattr(
        "capture.frame_worker.notify_fall",
        lambda label: notified.append(label),
    )

    worker = FrameWorker(frame_rate=2, classifier=clf)
    worker.insert_raw_frame(_frame(), 1.0)
    worker.raw_frame_queue.put_nowait(None)
    worker.run()

    assert notified == ["NORMAL", "SUSPECT", "FALL"]


def test_get_worker_ComSettingsPadrao_RetornaWorkerConfigurado(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    monkeypatch.setenv("FRAME_RATE", "5")
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    get_settings.cache_clear()
    get_worker.cache_clear()

    monkeypatch.setattr(
        "capture.frame_worker.create_classifier",
        lambda _cid=None: _mock_classifier(),
    )
    monkeypatch.setattr(
        "capture.frame_worker.get_classifier_id",
        lambda: "math",
    )

    worker = get_worker()

    assert worker.raw_frame_queue.maxsize == 5


def test_FrameWorker_stop_InsereSentinel() -> None:
    worker = FrameWorker(frame_rate=2, classifier=_mock_classifier())
    worker.stop()
    assert worker.raw_frame_queue.get_nowait() is None
