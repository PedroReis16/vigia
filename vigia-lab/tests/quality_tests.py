import numpy as np

from vigia_lab.quality import Thresholds, compute_quality, verdict


def _q(fps=12.0, seconds=10.0, torso=None, brightness=120.0, tracks=1, drops=0, **kw):
    n = int(fps * seconds)
    t = np.arange(n) / fps
    torso = np.ones(n, bool) if torso is None else torso(n, t)
    return compute_quality(
        t, np.ones(n, bool), np.full(n, 20.0), torso, np.full(n, brightness),
        tracks, 0.8, 30.0, video_drops=drops, **kw,
    )


def test_pose_fps_measured_from_timestamps() -> None:
    assert _q(fps=12.0)["pose_fps"] == np.float64(12.0) or abs(_q(fps=12.0)["pose_fps"] - 12.0) < 0.2


def test_green_when_everything_ok() -> None:
    color, reasons = verdict(_q())
    assert color == "verde" and reasons


def test_red_when_fps_low() -> None:
    color, reasons = verdict(_q(fps=6.0))
    assert color == "vermelho" and "fps" in reasons[0]


def test_yellow_when_fps_borderline_or_dark() -> None:
    assert verdict(_q(fps=10.0))[0] == "amarelo"
    assert verdict(_q(brightness=30.0))[0] == "amarelo"


def test_torso_gap_during_event_is_red() -> None:
    def torso(n, t):
        v = np.ones(n, bool)
        v[(t > 5.0) & (t < 6.0)] = False
        return v

    q = _q(torso=torso, event_window=(4.0, 7.0))
    assert q["max_torso_gap_in_event_s"] > 0.5
    assert verdict(q)[0] == "vermelho"


def test_gap_outside_event_is_only_yellow() -> None:
    def torso(n, t):
        v = np.ones(n, bool)
        v[(t > 1.0) & (t < 2.0)] = False
        return v

    assert verdict(_q(torso=torso, event_window=(4.0, 7.0)))[0] == "amarelo"


def test_too_few_frames_is_red() -> None:
    q = _q(fps=12.0, seconds=1.0)
    assert verdict(q, Thresholds(min_frames=30))[0] == "vermelho"


def test_multiple_tracks_and_video_drops_warn() -> None:
    color, reasons = verdict(_q(tracks=3, drops=2))
    assert color == "amarelo" and len(reasons) == 2


def test_low_delivered_fps_warns_even_if_pose_fps_ok() -> None:
    q = _q(fps=12.0)
    q["delivered_fps"] = 8.0
    color, reasons = verdict(q)
    assert color == "amarelo" and "entregues" in reasons[0]


def test_id_changes_warn() -> None:
    q = _q()
    q["id_set_changes_delivered"] = 2
    color, reasons = verdict(q)
    assert color == "amarelo" and "ID" in reasons[0]


def test_timing_summary_identifies_source_bound_and_cpu_bound() -> None:
    from vigia_lab.quality import timing_summary

    n = 100
    t = np.arange(n) * 0.075                                   # 75 ms entre frames
    cpu = np.full(n, 30.0)
    # camera/tracker: YOLO 20 ms, nosso 10 ms, mas o resultado demora 60 ms para chegar
    s = timing_summary(t, np.full(n, 60.0), np.full(n, 20.0), np.full(n, 10.0), cpu)
    assert s["bottleneck"] == "espera pela camera/tracker" and 39 < s["source_wait_ms_mean"] < 41
    # CPU: YOLO 50 ms + nosso 15 ms em 75 ms de intervalo
    s = timing_summary(t, np.full(n, 52.0), np.full(n, 50.0), np.full(n, 15.0), cpu)
    assert s["bottleneck"] == "processamento (CPU)" and s["busy_frac"] > 0.8
