"""Configuração do worker a partir de env / .env."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_POOL_PATH = ROOT_DIR / "device_pool.json"
DEFAULT_ASSETS_DIR = ROOT_DIR / "assets" / "videos"


@dataclass(frozen=True, slots=True)
class DeviceInfo:
    id: str
    name: str
    nickname: str
    mac_address: str
    room: str


@dataclass(frozen=True, slots=True)
class Settings:
    api_base_url: str
    fiware_api_key: str
    stream_ingest_url: str
    redis_url: str
    device_id: str | None
    assets_dir: Path
    pool_path: Path
    fall_min_s: float
    fall_max_s: float
    clip_window_s: float
    thumb_interval_s: float
    claim_ttl_s: int
    log_level: str


def load_settings(env_file: Path | None = None) -> Settings:
    load_dotenv(env_file or (ROOT_DIR / ".env"), override=False)

    fall_min = float(os.getenv("FALL_MIN_S", "300"))
    fall_max = float(os.getenv("FALL_MAX_S", "900"))
    if fall_max < fall_min:
        fall_max = fall_min

    device_id = (os.getenv("DEVICE_ID") or "").strip() or None
    assets = Path(os.getenv("ASSETS_DIR", str(DEFAULT_ASSETS_DIR))).expanduser()
    pool = Path(os.getenv("DEVICE_POOL_PATH", str(DEFAULT_POOL_PATH))).expanduser()

    return Settings(
        api_base_url=os.getenv("API_BASE_URL", "http://localhost:81/vigia").rstrip("/"),
        fiware_api_key=os.getenv("FIWARE_API_KEY", "VIGIA"),
        stream_ingest_url=os.getenv("STREAM_INGEST_URL", "rtmp://localhost:1935").rstrip("/"),
        redis_url=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
        device_id=device_id,
        assets_dir=assets,
        pool_path=pool,
        fall_min_s=fall_min,
        fall_max_s=fall_max,
        clip_window_s=float(os.getenv("CLIP_WINDOW_S", "10")),
        thumb_interval_s=float(os.getenv("THUMB_INTERVAL_S", "60")),
        claim_ttl_s=int(os.getenv("CLAIM_TTL_S", "30")),
        log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
    )


def load_device_pool(path: Path | None = None) -> list[DeviceInfo]:
    pool_path = path or DEFAULT_POOL_PATH
    payload = json.loads(pool_path.read_text(encoding="utf-8"))
    devices = payload.get("devices")
    if not isinstance(devices, list) or not devices:
        raise ValueError(f"device_pool vazio ou inválido: {pool_path}")

    result: list[DeviceInfo] = []
    for entry in devices:
        result.append(
            DeviceInfo(
                id=str(entry["id"]),
                name=str(entry["name"]),
                nickname=str(entry.get("nickname", entry["name"])),
                mac_address=str(entry.get("mac_address", "")),
                room=str(entry.get("room", "")),
            )
        )
    return result


def list_videos(assets_dir: Path) -> list[Path]:
    if not assets_dir.is_dir():
        return []
    return sorted(
        path
        for path in assets_dir.iterdir()
        if path.is_file() and path.suffix.lower() in {".mp4", ".avi", ".mkv", ".mov"}
    )
