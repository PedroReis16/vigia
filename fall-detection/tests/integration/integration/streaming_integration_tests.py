"""Integração: runner de streaming monta URL RTMP e delega ao worker."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from app.streaming.runner import run_streaming

from .integration_settings_helpers import minimal_integration_settings


@pytest.mark.integration
def test_run_streaming_should_pass_device_scoped_rtmp_url_to_worker_process(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Valida ingest base + device_id sem FFmpeg nem ZMQ reais."""

    device_id = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
    captured: list[tuple[object, tuple]] = []

    class CaptureProcess:
        def __init__(self, target=None, args=(), **kwargs: object) -> None:
            captured.append((target, args))

        def start(self) -> None:
            return None

        def is_alive(self) -> bool:
            return False

        def terminate(self) -> None:
            return None

        def join(self, timeout: float | None = None) -> None:
            return None

    monkeypatch.setattr(
        "app.streaming.runner.load_local_device_settings_required",
        lambda: MagicMock(device_id=device_id),
    )
    monkeypatch.setattr("app.streaming.runner.Process", CaptureProcess)

    logged_info: list[str] = []

    monkeypatch.setattr(
        "app.streaming.runner.logger.info",
        lambda msg, *a: logged_info.append(str(msg)),
    )

    settings = minimal_integration_settings(
        stream_ingest_url="rtmp://ingest.example/live",
    )

    run_streaming(settings)

    assert captured, "Process deveria ser instanciado com target=_consume_frames"
    target, args = captured[0]
    assert args == (f"rtmp://ingest.example/live/{device_id}",)
    assert any("finalizado" in m.lower() for m in logged_info)
