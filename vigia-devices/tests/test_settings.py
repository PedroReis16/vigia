from __future__ import annotations

import json
from pathlib import Path

import pytest

from worker.settings import load_device_pool, list_videos


def test_load_device_pool_excludes_edge_test_device():
    pool = load_device_pool()
    assert len(pool) == 7
    ids = {device.id for device in pool}
    assert len(ids) == 7
    assert "b7e3c9a1-4f2d-4e8b-9c1a-6d5e4f3a2b1c" not in ids
    assert pool[0].id == "a1b2c3d4-e5f6-4789-a012-3456789abcde"


def test_load_device_pool_rejects_reserved_edge_id(tmp_path: Path):
    payload = {
        "devices": [
            {
                "id": "b7e3c9a1-4f2d-4e8b-9c1a-6d5e4f3a2b1c",
                "name": "Vigia-a1b2c3d4",
                "nickname": "Edge",
                "mac_address": "AA:BB:CC:DD:EE:FF",
                "room": "LivingRoom",
            }
        ],
        "reserved_edge_ids": ["b7e3c9a1-4f2d-4e8b-9c1a-6d5e4f3a2b1c"],
    }
    path = tmp_path / "pool.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="reservado ao edge real"):
        load_device_pool(path)


def test_load_device_pool_from_custom_file(tmp_path: Path):
    payload = {
        "devices": [
            {
                "id": "11111111-1111-4111-8111-111111111111",
                "name": "Vigia-11111111",
                "nickname": "One",
                "mac_address": "AA:BB:CC:DD:EE:11",
                "room": "Office",
            }
        ]
    }
    path = tmp_path / "pool.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    pool = load_device_pool(path)
    assert len(pool) == 1
    assert pool[0].nickname == "One"


def test_list_videos_filters_extensions(tmp_path: Path):
    (tmp_path / "a.mp4").write_bytes(b"x")
    (tmp_path / "b.avi").write_bytes(b"x")
    (tmp_path / "c.txt").write_bytes(b"x")
    videos = list_videos(tmp_path)
    assert [path.name for path in videos] == ["a.mp4", "b.avi"]
