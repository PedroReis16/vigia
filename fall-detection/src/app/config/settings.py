"""Configuração a partir de variáveis de ambiente."""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

from app.config.ingest import tcp_stream_target_from_env
from app.logging import get_logger

logger = get_logger("config")


@dataclass(frozen=True)
class Settings:  # pylint: disable=too-many-instance-attributes
    """Parâmetros da aplicação carregados de variáveis de ambiente (.env)."""
    data_path: str | None
    stream_ingest_url: str
    captures_per_second: int
    video_capture_source: int | str
    show_video: bool
    yolo_pose_model: str | None
    pose_csv_window_seconds: float
    integration_interval_seconds: int

    @property
    def capture_interval(self) -> float | None:
        """Intervalo em segundos entre capturas automáticas, ou None se desligado."""
        if self.captures_per_second <= 0:
            return None
        return 1.0 / self.captures_per_second

    @classmethod
    def from_env(cls) -> Settings:
        """Lê `.env` e variáveis de ambiente e monta `Settings`."""
        load_dotenv()

        data_path = (os.getenv("DATA_PATH") or "").strip() or "data"

        stream_ingest_url = (os.getenv("STREAM_INGEST_URL") or "").strip()


        show_video = _env_truthy("SHOW_VIDEO")
        captures_per_second = int(os.getenv("CAPTURES_PER_SECOND", "0"))
        video_source = _video_capture_source()

        yolo_pose_model = os.getenv("YOLO_POSE_MODEL")
        pose_csv_window_seconds = float(os.getenv("POSE_CSV_WINDOW_SECONDS", "3"))
        integration_interval_seconds = int(os.getenv("INTEGRATION_INTERVAL_SECONDS", "3"))
        
        return cls(
            data_path=data_path,
            pose_csv_window_seconds=pose_csv_window_seconds,
            video_capture_source=video_source,
            captures_per_second=captures_per_second,
            stream_ingest_url=stream_ingest_url,

            yolo_pose_model=yolo_pose_model,
            integration_interval_seconds=integration_interval_seconds,
            show_video=show_video,
        )


def _env_truthy(name: str) -> bool:
    """Aceita True/1/yes/on (case-insensitive) como em .env com SHOW_VIDEO=True."""
    v = (os.getenv(name) or "").strip().lower()
    return v in ("1", "true", "yes", "on")


def _video_capture_source() -> int | str:
    """
    Fonte para cv2.VideoCapture:
    - número (ex.: 0, 1): índice do dispositivo;
    - URL: http://... ou rtsp://...
    """
    raw = (os.getenv("VIDEO_CAPTURE_SOURCE") or "0").strip()
    if not raw:
        return 0
    if raw.isdigit():
        return int(raw)
    return raw
