import numpy as np

from vigia_lab.resample import nearest_indices, time_grid
from vigia_lab.throttle import Throttle


def test_time_grid_is_ascending_and_ends_at_t_end() -> None:
    g = time_grid(10.0)
    assert len(g) == 20
    assert g[-1] == 10.0
    np.testing.assert_allclose(np.diff(g), 0.1)


def test_nearest_indices_marks_gaps_with_minus_one() -> None:
    times = np.array([0.0, 0.1, 0.2, 1.0, 1.1])
    grid = np.array([0.0, 0.1, 0.5, 1.05])
    idx = nearest_indices(times, grid, tolerance=0.15)
    assert idx[0] == 0 and idx[1] == 1
    assert idx[2] == -1          # 0,5 s está a >0,15 s de qualquer amostra
    assert idx[3] in (3, 4)


def test_nearest_indices_empty_history() -> None:
    assert (nearest_indices(np.array([]), np.array([1.0, 2.0])) == -1).all()


def test_throttle_matches_onboard_frame_queue(monkeypatch) -> None:
    import core.frame_queue as fq_mod

    now = [1000.0]  # monotonic real é grande; evita o caso 'último=0.0' do FrameQueue
    monkeypatch.setattr(fq_mod.time, "monotonic", lambda: now[0])
    queue = fq_mod.FrameQueue(12, maxsize=10_000)
    throttle = Throttle(12, clock=lambda: now[0])

    rng = np.random.default_rng(0)
    for dt in rng.uniform(0.01, 0.15, size=300):
        now[0] += float(dt)
        assert throttle.accept() == queue.push([]), f"divergiu em t={now[0]:.3f}"
