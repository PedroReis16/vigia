"""
Seed local: publica um frame JPEG em POST /vigia/devices/{deviceId}/frame.

Deps: pip install -r requirements.txt
"""

from __future__ import annotations

import uuid
from pathlib import Path

import requests

# --- config (espelha Vigia.Models.Seed.TestDeviceSeed) ---
BASE_URL = "http://localhost:8090/vigia"
DEVICE_ID = "b7e3c9a1-4f2d-4e8b-9c1a-6d5e4f3a2b1c"
FRAME_PATH = Path(__file__).parent / "assets" / "frame.jpg"

_MIN_JPEG = bytes.fromhex(
    "ffd8ffe000104a46494600010100000100010000"
    "ffdb004300080606070605080707070909080a0c140d0c0b0b0c1912130f141d1a1f1e1d1a1c1c20242e2720222c231c1c2837292c30313434341f27393d38323c2e333432"
    "ffdb0043010909090c0b0c180d0d1832211c213232323232323232323232323232323232323232323232323232323232323232323232323232323232323232323232323232"
    "ffc00011080001000103011100021100031100"
    "ffc40014000100000000000000000000000000000000"
    "ffc40014100100000000000000000000000000000000"
    "ffda000c0301000210031000003f00bf80"
    "ffd9"
)


def _jpeg_bytes() -> bytes:
    if FRAME_PATH.is_file():
        return FRAME_PATH.read_bytes()
    return _MIN_JPEG


def publish_frame() -> None:
    device_id = uuid.UUID(DEVICE_ID)
    url = f"{BASE_URL}/devices/{device_id}/frame"
    filename = FRAME_PATH.name if FRAME_PATH.is_file() else "frame.jpg"
    resp = requests.post(
        url,
        files={"frameFile": (filename, _jpeg_bytes(), "image/jpeg")},
        timeout=30,
    )
    print(f"{resp.status_code} {resp.reason}")
    if resp.content:
        print(resp.text)


if __name__ == "__main__":
    publish_frame()
