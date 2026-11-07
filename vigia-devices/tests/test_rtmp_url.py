from __future__ import annotations

import pytest

from worker.rtmp import rtmp_publish_url


def test_rtmp_publish_url_builds_live_path():
    assert (
        rtmp_publish_url("rtmp://localhost:1935", "b7e3c9a1-4f2d-4e8b-9c1a-6d5e4f3a2b1c")
        == "rtmp://localhost:1935/live/b7e3c9a1-4f2d-4e8b-9c1a-6d5e4f3a2b1c"
    )


def test_rtmp_publish_url_rejects_path_in_ingest():
    with pytest.raises(ValueError, match="somente esquema"):
        rtmp_publish_url("rtmp://localhost:1935/live", "id")
