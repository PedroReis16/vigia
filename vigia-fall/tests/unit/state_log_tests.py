"""Testes de STATE_LOG_MODE e política de logs de decisão."""

from __future__ import annotations

import logging
from unittest.mock import MagicMock

import pytest

from capture.classifiers.types import FallDecision
from capture.frame_worker import FrameWorker
from shared.log_bridge import should_emit


def _mock_classifier(decisions: list[FallDecision]) -> MagicMock:
    clf = MagicMock()
    clf.process.return_value = decisions
    return clf


def test_verbose_emite_todas_decisoes(monkeypatch: pytest.MonkeyPatch) -> None:
    logged: list[str] = []

    def capture_log(level, message, *, capture_ts=0.0, person_id=0):
        if level >= logging.INFO:
            logged.append(message)

    monkeypatch.setattr("capture.frame_worker.extract_poses", lambda _f, _d: [MagicMock()])
    monkeypatch.setattr("capture.frame_worker.emit_log", capture_log)
    monkeypatch.setattr("capture.frame_worker.enqueue_fall_state", lambda *a, **k: None)

    clf = _mock_classifier(
        [
            FallDecision(person_id=1, label="NORMAL", alert=False, detail={"score": 0.1}),
            FallDecision(person_id=1, label="NORMAL", alert=False, detail={"score": 0.2}),
        ]
    )
    worker = FrameWorker(frame_rate=2, classifier=clf, state_log_mode="verbose")
    worker.insert_raw_frame(MagicMock(), 1.0)
    worker.raw_frame_queue.put_nowait(None)
    worker.run()

    assert len(logged) == 2
    assert all("state Person 1: NORMAL" in msg for msg in logged)
    assert "score=0.10" in logged[0] or "score=0.1" in logged[0]


def test_changes_dedupe_repetidas(monkeypatch: pytest.MonkeyPatch) -> None:
    logged: list[str] = []

    monkeypatch.setattr("capture.frame_worker.extract_poses", lambda _f, _d: [MagicMock()])
    monkeypatch.setattr(
        "capture.frame_worker.emit_log",
        lambda level, message, **_: logged.append(message) if level >= logging.INFO else None,
    )
    monkeypatch.setattr("capture.frame_worker.enqueue_fall_state", lambda *a, **k: None)

    clf = _mock_classifier(
        [
            FallDecision(person_id=1, label="NORMAL", alert=False),
            FallDecision(person_id=1, label="NORMAL", alert=False),
            FallDecision(person_id=1, label="SUSPECT", alert=False),
        ]
    )
    worker = FrameWorker(frame_rate=2, classifier=clf, state_log_mode="changes")
    worker.insert_raw_frame(MagicMock(), 1.0)
    worker.raw_frame_queue.put_nowait(None)
    worker.run()

    assert logged == [
        "state Person 1: NORMAL",
        "state Person 1: SUSPECT",
    ]


def test_heartbeat_repete_apos_intervalo(monkeypatch: pytest.MonkeyPatch) -> None:
    logged: list[tuple[str, float]] = []

    monkeypatch.setattr("capture.frame_worker.extract_poses", lambda _f, _d: [MagicMock()])
    monkeypatch.setattr(
        "capture.frame_worker.emit_log",
        lambda level, message, *, capture_ts=0.0, **_: logged.append((message, capture_ts))
        if level >= logging.INFO
        else None,
    )
    monkeypatch.setattr("capture.frame_worker.enqueue_fall_state", lambda *a, **k: None)

    clf = _mock_classifier(
        [
            FallDecision(person_id=1, label="NORMAL", alert=False),
            FallDecision(person_id=1, label="NORMAL", alert=False),
        ]
    )
    worker = FrameWorker(
        frame_rate=2,
        classifier=clf,
        state_log_mode="heartbeat",
        state_log_interval_s=2.0,
    )

    worker._log_decision(clf.process.return_value[0], 1.0)
    worker._log_decision(clf.process.return_value[0], 1.5)
    worker._log_decision(clf.process.return_value[0], 3.5)

    assert len(logged) == 2
    assert logged[0][1] == 1.0
    assert logged[1][1] == 3.5


def test_verbose_no_person(monkeypatch: pytest.MonkeyPatch) -> None:
    logged: list[str] = []
    monkeypatch.setattr("capture.frame_worker.extract_poses", lambda _f, _d: [])
    monkeypatch.setattr(
        "capture.frame_worker.emit_log",
        lambda _l, message, **_: logged.append(message),
    )

    worker = FrameWorker(frame_rate=2, classifier=_mock_classifier([]), state_log_mode="verbose")
    worker.insert_raw_frame(MagicMock(), 2.0)
    worker.raw_frame_queue.put_nowait(None)
    worker.run()

    assert logged == ["state no_person: frame ok, zero poses"]


def test_should_emit_respeita_nivel_root(caplog) -> None:
    root = logging.getLogger()
    old = root.level
    root.setLevel(logging.INFO)
    try:
        assert should_emit(logging.INFO) is True
        assert should_emit(logging.DEBUG) is False
    finally:
        root.setLevel(old)
