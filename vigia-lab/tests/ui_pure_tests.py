import numpy as np

from vigia_lab import hud
from vigia_lab.catalog import load_catalog
from vigia_lab.menu import MenuState
from vigia_lab.ui import translate_key
from vigia_lab.video_sink import VideoSink


def test_menu_navigation_wraps_and_filters() -> None:
    m = MenuState(load_catalog())
    assert m.handle("up") == "none" and m.index == 15            # volta ao fim
    m.index = 0
    assert m.handle("tab") == "none" and m.only == "FALL"
    assert len(m.visible) == 5 and m.selected.is_fall
    assert m.handle("tab") == "none" and m.only == "ADL"
    assert all(not s.is_fall for s in m.visible)
    assert m.handle("enter") == "start" and m.handle("esc") == "quit"


def test_translate_key() -> None:
    assert translate_key(13) == "enter" and translate_key(2621440) == "down"
    assert translate_key(ord("m")) == "m" and translate_key(-1) == ""


def test_latest_by_model_flashes_only_recent_alerts() -> None:
    dec = [
        {"model": "gru34", "label": "FALL", "alert": 1, "prob_fall": "0.9", "score": "", "t_rel": 1.0},
        {"model": "math", "label": "NORMAL", "alert": 0, "prob_fall": "", "score": "0.2", "t_rel": 4.0},
    ]
    cards = hud.latest_by_model(dec, t_now=2.0)
    assert cards["gru34"]["flash"] and cards["gru34"]["extra"].startswith("p(queda)")
    assert not hud.latest_by_model(dec, t_now=5.0)["gru34"]["flash"]
    assert cards["math"]["extra"].startswith("score")


def test_drawing_does_not_crash_and_has_expected_size() -> None:
    img = np.full((480, 640, 3), 90, dtype=np.uint8)
    kp = np.zeros((17, 3), dtype=np.float32)
    kp[:, :2] = 200.0
    kp[:, 2] = 0.9
    for phase in ("countdown", "recording"):
        out = hud.draw_live(img, [kp], phase, 2.5, 10.0, "sentando", "ADL", 1, 12.0,
                            {"gru34": {"label": "FALL", "extra": "p(queda) 0.9", "flash": True}}, 1, True)
        assert out.shape == (hud.H, hud.W, 3)
    assert hud.draw_menu([("a", "ADL", 1), ("b", "FALL", 2)], 1, None).shape == (hud.H, hud.W, 3)
    q = {"pose_fps": 12.0, "delivered_fps": 9.0, "n_tracks": 1, "torso_valid_frac": 0.9}
    assert hud.draw_summary("amarelo", ["fps limitrofe"], q, "a", 1).shape == (hud.H, hud.W, 3)


def test_video_sink_writes_frames_and_counts_drops(tmp_path) -> None:
    path = tmp_path / "t.avi"
    sink = VideoSink(path, 10.0, (64, 48))
    for _ in range(5):
        sink.write(np.full((48, 64, 3), 128, dtype=np.uint8))
    sink.close()
    assert sink.written == 5 and sink.drops == 0 and path.stat().st_size > 0
