from pathlib import Path

import numpy as np

from vigia_lab.quick_check import summarize_samples, torso_visible
from vigia_lab.recordings import Recording, append_recording, read_recordings, takes_recorded
from vigia_lab.takes import takes_from_videos


def _person(torso=True):
    kp = np.zeros((17, 3), dtype=np.float32)
    kp[:, 2] = 0.9
    if not torso:
        kp[[5, 6, 11, 12], 2] = 0.1
    return kp


def test_torso_visible_uses_vigia_threshold() -> None:
    assert torso_visible(_person()) and not torso_visible(_person(torso=False))


def test_summarize_samples() -> None:
    s = summarize_samples([[_person()], [_person(), _person()], [], [_person(torso=False)]])
    assert s["sampled"] == 4 and s["torso_valid_frac"] == 0.5 and s["n_tracks"] == 2
    assert summarize_samples([]) == {"sampled": 0, "torso_valid_frac": 0.0, "n_tracks": 0}


def test_takes_from_videos_and_recordings_csv(tmp_path: Path) -> None:
    for n in ("sentando_take01.avi", "sentando_take03.avi", "sentando_take03_frames.npz", "outro_take09.avi"):
        (tmp_path / n).touch()
    assert takes_from_videos(tmp_path, "sentando") == {1, 3}

    csv_path = tmp_path / "recordings.csv"
    rec = Recording("sentando_take01", "sentando", "ADL", 1, "s1", Path("a.avi"), Path("a.npz"), Path("a.json"),
                    300, 10.0, 29.8, "verde", event_start_t=2.5)
    append_recording(csv_path, rec)
    rows = read_recordings(csv_path)
    assert rows[0]["event_start_t"] == "2.5" and rows[0]["event_end_t"] == "" and takes_recorded(csv_path, "sentando") == {1}
