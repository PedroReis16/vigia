"""Configuração a partir de variáveis de ambiente."""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

from app.config.ingest import tcp_stream_target_from_env


@dataclass(frozen=True)
class Settings:
    data_path: str | None
    frames_dir: str | None
    stream_ingest_url: str
    stream_ingest_token: str
    stream_target: tuple[str, int] | None
    captures_per_second: int
    video_capture_source: int | str
    show_video: bool
    
    @property
    def capture_interval(self) -> float | None:
        if self.captures_per_second <= 0:
            return None
        return 1.0 / self.captures_per_second

    @classmethod
    def from_env(cls) -> Settings:
        load_dotenv()
        data_path = (os.getenv("DATA_PATH") or "").strip() or None
        frames_dir: str | None
        if data_path:
            frames_dir = os.path.join(data_path.rstrip("/"), "frames")
            os.makedirs(frames_dir, exist_ok=True)
        else:
            frames_dir = None

        stream_video = _env_truthy("STREAM_VIDEO")

        stream_ingest_url = (os.getenv("STREAM_INGEST_URL") or "").strip()
        stream_ingest_token = (os.getenv("STREAM_INGEST_TOKEN") or "").strip()
        stream_target = tcp_stream_target_from_env()

        if stream_video and not stream_ingest_url and stream_target is None:
            print(
                "Aviso: defina STREAM_INGEST_URL=https://…/ingest (via Traefik) ou "
                "STREAM_TCP_ADDR=host:porta (TCP :8090).",
                flush=True,
            )

        show_video = _env_truthy("SHOW_VIDEO")
        captures_per_second = int(os.getenv("CAPTURES_PER_SECOND", "0"))
        video_source = _video_capture_source()

        return cls(
            data_path=data_path,
            frames_dir=frames_dir,
            stream_ingest_url=stream_ingest_url,
            stream_ingest_token=stream_ingest_token,
            stream_target=stream_target,
            captures_per_second=captures_per_second,
            video_capture_source=video_source,
            show_video=show_video
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
