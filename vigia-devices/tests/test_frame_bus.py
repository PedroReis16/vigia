from __future__ import annotations

import numpy as np

from worker.frame_bus import FrameBus


def test_frame_bus_keeps_latest_and_clip_window():
    bus = FrameBus(clip_window_s=1.0, default_fps=5.0)
    for index in range(10):
        frame = np.full((4, 4, 3), index, dtype=np.uint8)
        bus.push(frame)

    latest = bus.latest()
    assert latest is not None
    assert int(latest[0, 0, 0]) == 9

    clip = bus.snapshot_clip()
    assert len(clip) == 6  # 1s * 5fps + 1
    assert int(clip[0][0, 0, 0]) == 4
    assert int(clip[-1][0, 0, 0]) == 9
