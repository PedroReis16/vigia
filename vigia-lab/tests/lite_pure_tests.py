import numpy as np

from vigia_lab.cadence import select_frames
from vigia_lab.capture_quality import capture_metrics, capture_verdict
from vigia_lab.marks import DurationPolicy, EventMarks


def test_select_frames_keeps_every_third_frame_at_30fps_to_10fps() -> None:
    t = np.arange(90) / 30.0
    idx = select_frames(t, 10.0)
    assert len(idx) == 30 and idx[:4].tolist() == [0, 3, 6, 9]


def test_select_frames_is_noop_when_pose_fps_exceeds_camera_fps() -> None:
    t = np.arange(60) / 30.0
    assert select_frames(t, 60.0).tolist() == list(range(60))


def test_select_frames_gives_the_requested_average_rate_even_with_jitter() -> None:
    rng = np.random.default_rng(1)
    t = np.cumsum(np.full(900, 1 / 30.0) + rng.normal(0, 1e-4, 900))      # 30 s com jitter de 0,1 ms
    idx = select_frames(t, 10.0)
    rate = (len(idx) - 1) / (t[idx[-1]] - t[idx[0]])
    assert 9.8 < rate < 10.2
    assert set(np.diff(idx).tolist()) == {3}                              # sem arredondar para 4 frames


def test_select_frames_uses_real_timestamps_not_indices() -> None:
    # camera a ~15 fps (45 frames = 3 s): a 10 fps médios o dispositivo pega 2 de cada 3 frames
    t = np.arange(45) / 15.0
    idx = select_frames(t, 10.0)
    assert 28 <= len(idx) <= 31
    assert set(np.diff(idx).tolist()) <= {1, 2}


def test_marks_start_end_undo() -> None:
    m = EventMarks()
    assert not m.press_end(1.0)                  # fim sem início é ignorado
    assert m.press_start(2.0) and m.press_end(3.5)
    assert m.as_dict() == {"event_start_t": 2.0, "event_end_t": 3.5}
    assert not m.press_end(1.0)                  # fim antes do início
    assert m.undo() and m.end_t is None and m.start_t == 2.0
    assert m.undo() and m.start_t is None
    assert not m.undo()


def test_redefining_start_after_end_drops_invalid_end() -> None:
    m = EventMarks()
    m.press_start(2.0)
    m.press_end(3.0)
    m.press_start(4.0)                           # recomeçou depois do fim antigo
    assert m.start_t == 4.0 and m.end_t is None


def test_duration_policy_fixed_and_manual() -> None:
    fixed = DurationPolicy()
    assert not fixed.finished(9.9, False) and fixed.finished(10.0, False) and fixed.finished(1.0, True)
    assert fixed.remaining(4.0) == 6.0
    manual = fixed.toggled()
    assert manual.mode == "manual" and not manual.finished(60.0, False)
    assert manual.finished(1.0, True) and manual.remaining(1.0) is None
    assert manual.toggled().mode == "fixed"


def _metrics(fps=30.0, seconds=10.0, brightness=120.0, dropped=0):
    n = int(fps * seconds)
    return capture_metrics(np.arange(n) / fps, np.full(n, brightness), dropped, 30.0)


def test_capture_verdict_levels() -> None:
    assert capture_verdict(_metrics())[0] == "verde"
    assert capture_verdict(_metrics(fps=22.0))[0] == "amarelo"
    assert capture_verdict(_metrics(fps=14.0))[0] == "vermelho"
    assert capture_verdict(_metrics(brightness=30.0))[0] == "amarelo"
    assert capture_verdict(_metrics(dropped=3))[0] == "amarelo"
    assert capture_verdict(_metrics(dropped=100))[0] == "vermelho"


def test_capture_verdict_uses_pose_check() -> None:
    m = _metrics()
    assert capture_verdict(m, {"torso_valid_frac": 0.95, "n_tracks": 1})[0] == "verde"
    assert capture_verdict(m, {"torso_valid_frac": 0.7, "n_tracks": 1})[0] == "amarelo"
    color, reasons = capture_verdict(m, {"torso_valid_frac": 0.0, "n_tracks": 0})
    assert color == "vermelho" and "tronco" in reasons[0]
