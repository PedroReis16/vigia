from __future__ import annotations

from worker.fall_sim import next_fall_delay


def test_next_fall_delay_within_range():
    for _ in range(20):
        delay = next_fall_delay(10, 20)
        assert 10 <= delay <= 20


def test_next_fall_delay_swaps_inverted_range():
    delay = next_fall_delay(50, 10)
    assert delay == 50
