"""Testes de integração leves para o fluxo de análise (app.core)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from app.config import Settings
from app.core import run_analysis, run_classifier, run_frame_consumer


def test_core_package_exports_runners() -> None:
    assert callable(run_analysis)
    assert callable(run_frame_consumer)
    assert callable(run_classifier)


def test_run_analysis_end_to_end_with_stub_processes_should_complete() -> None:
    """Garante que preparação + spawn + join encerram sem subprocessos reais."""

    settings = Settings(
        data_path="data",
        stream_ingest_url="",
        captures_per_second=5,
        video_capture_source=0,
        show_video=False,
        yolo_pose_model="stub-pose.pt",
        pose_csv_window_seconds=3.0,
        integration_interval_seconds=30,
    )

    class StubProcess:
        def __init__(self, *_a: object, **_k: object) -> None:
            pass

        def start(self) -> None:
            return None

        def is_alive(self) -> bool:
            return False

        def terminate(self) -> None:
            return None

        def join(self, _timeout: float | None = None) -> None:
            return None

    with (
        patch("app.core.runner.load_local_device_settings_required"),
        patch("app.core.runner.prepare_data_workspace"),
        patch("app.core.runner.YOLO", return_value=MagicMock()),
        patch("app.core.runner.Process", StubProcess),
        patch("app.core.runner.signal.signal"),
    ):
        run_analysis(settings)
