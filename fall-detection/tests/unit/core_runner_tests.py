"""Testes unitários para o orquestrador de análise (app.core.runner)."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from app.config import Settings
from app.core.runner import run_analysis


def test_run_analysis_given_zero_captures_per_second_should_raise() -> None:
    settings = Settings(
        data_path="data",
        stream_ingest_url="",
        captures_per_second=0,
        video_capture_source=0,
        show_video=False,
        yolo_pose_model="yolo26s-pose.pt",
        pose_csv_window_seconds=3.0,
        integration_interval_seconds=60,
    )

    with (
        patch("app.core.runner.load_local_device_settings_required"),
        patch("app.core.runner.prepare_data_workspace"),
        pytest.raises(ValueError, match="Captures por segundo"),
    ):
        run_analysis(settings)


def test_run_analysis_given_valid_settings_should_start_worker_processes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = Settings(
        data_path="data",
        stream_ingest_url="",
        captures_per_second=10,
        video_capture_source=0,
        show_video=False,
        yolo_pose_model="yolo26s-pose.pt",
        pose_csv_window_seconds=3.0,
        integration_interval_seconds=60,
    )

    started: list[tuple[object, tuple[object, ...]]] = []

    class DummyProcess:
        def __init__(self, target: object, args: tuple[object, ...], daemon: bool) -> None:
            self._target = target
            self._args = args
            self.daemon = daemon

        def start(self) -> None:
            started.append((self._target, self._args))

        def is_alive(self) -> bool:
            return False

        def terminate(self) -> None:
            return None

        def join(self, _timeout: float | None = None) -> None:
            return None

    monkeypatch.setattr("app.core.runner.Process", DummyProcess)

    fake_pose = object()

    with (
        patch("app.core.runner.load_local_device_settings_required"),
        patch("app.core.runner.prepare_data_workspace"),
        patch("app.core.runner.YOLO", return_value=fake_pose),
    ):
        run_analysis(settings)

    assert len(started) == 2
    targets = {t for t, _ in started}
    from app.core.action_classifier import run_classifier
    from app.core.frame_consumer import run_frame_consumer

    assert run_frame_consumer in targets
    assert run_classifier in targets

    consumer_args = next(a for t, a in started if t is run_frame_consumer)
    assert consumer_args[0] is fake_pose
    assert consumer_args[1] == settings.captures_per_second

    classifier_args = next(a for t, a in started if t is run_classifier)
    assert classifier_args[0].__class__.__name__ == "Queue"
