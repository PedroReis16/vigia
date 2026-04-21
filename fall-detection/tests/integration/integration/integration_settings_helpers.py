"""Helpers para montar Settings mínimos nos testes de integração."""

from __future__ import annotations

from app.config import Settings


def minimal_integration_settings(**overrides: object) -> Settings:
    """Settings estáveis para fluxos que só precisam de integration_interval_seconds."""
    base = dict(
        data_path=None,
        frames_dir=None,
        stream_video=False,
        stream_ingest_url="",
        stream_ingest_token="",
        stream_target=None,
        captures_per_second=0,
        video_capture_source=0,
        show_video=False,
        yolo_model=None,
        yolo_pose_model=None,
        yolo_model_device=None,
        pose_csv_window_seconds=3.0,
        integration_interval_seconds=60,
    )
    base.update(overrides)
    return Settings(**base)
