"""Helpers para montar Settings mínimos nos testes de integração."""

from __future__ import annotations

from app.config import Settings


def minimal_integration_settings(**overrides: object) -> Settings:
    """Settings estáveis para fluxos que só precisam de integration_interval_seconds."""
    base = dict(
        data_path="data",
        stream_ingest_url="",
        captures_per_second=0,
        video_capture_source=0,
        show_video=False,
        yolo_pose_model=None,
        pose_csv_window_seconds=3.0,
        integration_interval_seconds=60,
    )
    base.update(overrides)
    return Settings(**base)
