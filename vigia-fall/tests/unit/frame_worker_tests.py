"""Testes unitários para capture.frame_worker.FrameWorker."""

from __future__ import annotations

import logging
import threading
from unittest.mock import MagicMock

import numpy as np
import pytest

from capture.classifiers.types import FallDecision
from capture.frame_worker import FrameWorker, _format_window_fill, get_worker
from shared import get_settings


def _frame() -> np.ndarray:
    return np.zeros((4, 4, 3), dtype=np.uint8)


def _mock_classifier() -> MagicMock:
    clf = MagicMock()
    clf.process.return_value = []
    clf.get_window_fill.return_value = {1: (3, 20)}
    clf.window_capacity = 20
    return clf


def test_FrameWorker_insert_raw_frame_ComFilaDisponivel_ArmazenaFrame() -> None:
    worker = FrameWorker(frame_rate=2, classifier=_mock_classifier())
    frame = _frame()

    accepted = worker.insert_raw_frame(frame, 1.0)

    assert accepted is True
    assert worker.raw_frame_queue.qsize() == 1
    queued_frame, ts = worker.raw_frame_queue.queue[0]
    assert np.array_equal(queued_frame, frame)
    assert ts == 1.0


def test_FrameWorker_try_insert_raw_frame_ComFilaCheia_IgnoraFrame() -> None:
    worker = FrameWorker(frame_rate=1, classifier=_mock_classifier())
    frame_antigo = _frame()
    frame_novo = np.ones((4, 4, 3), dtype=np.uint8)
    worker.insert_raw_frame(frame_antigo, 1.0)

    accepted = worker.try_insert_raw_frame(frame_novo, 2.0)

    assert accepted is False
    assert worker.raw_frame_queue.qsize() == 1
    queued_frame, ts = worker.raw_frame_queue.queue[0]
    assert np.array_equal(queued_frame, frame_antigo)
    assert ts == 1.0
    assert worker._queue_skips == 1


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


def test_FrameWorker_enfileira_estados_com_dedupe(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    enqueued: list[tuple[str, float]] = []

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
        "capture.frame_worker.enqueue_fall_state",
        lambda label, capture_ts=0.0: enqueued.append((label, capture_ts)),
    )
    monkeypatch.setattr("capture.frame_worker.emit_log", lambda *a, **k: None)

    worker = FrameWorker(frame_rate=2, classifier=clf, state_log_mode="changes")
    worker.insert_raw_frame(_frame(), 1.0)
    worker.raw_frame_queue.put_nowait(None)
    worker.run()

    assert enqueued == [("NORMAL", 1.0), ("SUSPECT", 1.0), ("FALL", 1.0)]


def test_FrameWorker_loga_so_em_mudanca_de_label(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    logged: list[str] = []

    def fake_extract(frame, capture_date):
        return [MagicMock()]

    def capture_log(level, message, *, capture_ts=0.0, person_id=0):
        if level >= logging.INFO:
            logged.append(message)

    clf = MagicMock()
    clf.process.return_value = [
        FallDecision(person_id=1, label="NORMAL", alert=False),
        FallDecision(person_id=1, label="NORMAL", alert=False),
        FallDecision(person_id=1, label="SUSPECT", alert=False),
        FallDecision(person_id=2, label="NORMAL", alert=False),
    ]
    monkeypatch.setattr("capture.frame_worker.extract_poses", fake_extract)
    monkeypatch.setattr("capture.frame_worker.enqueue_fall_state", lambda *a, **k: None)
    monkeypatch.setattr("capture.frame_worker.emit_log", capture_log)

    worker = FrameWorker(frame_rate=2, classifier=clf, state_log_mode="changes")
    worker.insert_raw_frame(_frame(), 1.0)
    worker.raw_frame_queue.put_nowait(None)
    worker.run()

    assert logged == [
        "state Person 1: NORMAL",
        "state Person 1: SUSPECT",
        "state Person 2: NORMAL",
    ]


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

    assert worker.raw_frame_queue.maxsize == 2


def test_FrameWorker_stop_InsereSentinel() -> None:
    worker = FrameWorker(frame_rate=2, classifier=_mock_classifier())
    worker.stop()
    assert worker.raw_frame_queue.get_nowait() is None


def test_format_window_fill_ComPreenchimentoParcial() -> None:
    clf = MagicMock()
    clf.get_window_fill.return_value = {1: (7, 20)}
    assert _format_window_fill(clf) == "p1=7/20"


def test_format_window_fill_SemBuffer_UsaCapacidade() -> None:
    clf = MagicMock()
    clf.get_window_fill.return_value = {}
    clf.window_capacity = 30
    assert _format_window_fill(clf) == "window=0/30"


def test_FrameWorker_log_warmup_IncluiPreenchimentoDaJanela(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    logged: list[str] = []

    monkeypatch.setattr(
        "capture.frame_worker.extract_poses",
        lambda _f, _d: [MagicMock()],
    )
    monkeypatch.setattr(
        "capture.frame_worker.emit_log",
        lambda _l, message, **_: logged.append(message),
    )

    worker = FrameWorker(frame_rate=2, classifier=_mock_classifier(), state_log_mode="verbose")
    worker.insert_raw_frame(_frame(), 1.0)
    worker.raw_frame_queue.put_nowait(None)
    worker.run()

    assert logged == ["state warmup: poses=1 p1=3/20 janela incompleta"]
