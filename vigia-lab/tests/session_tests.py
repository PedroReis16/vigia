import json
from pathlib import Path

import numpy as np

from core.models.types import FallDecision, PoseObservation
from core.point_filter import filter_observations
from vigia_lab.manifest import read_entries
from vigia_lab.session import PoseFrame, TakeConfig, finalize_take, run_take


class FakeStore:
    def cleanup(self, ids):
        pass


class CountingClassifier:
    def __init__(self) -> None:
        self.calls = 0
        self.cleanups: list[set] = []

    def process(self, obs):
        self.calls += 1
        return [FallDecision(o.person_id, "ADL", False, {"probs": [0.9, 0.1]}) for o in obs]

    def cleanup(self, ids):
        self.cleanups.append(set(ids))


def _person(pid: int = 1) -> np.ndarray:
    kp = np.zeros((17, 3), dtype=np.float32)
    kp[:, :2] = 60.0
    kp[:, 2] = 0.9
    return kp


def _frames(fps: float, seconds: float, with_person=lambda i: True):
    img = np.full((48, 64, 3), 100, dtype=np.uint8)
    for i in range(int(fps * seconds)):
        t = 1000.0 + i / fps
        obs = [PoseObservation(1, _person(), t)] if with_person(i) else []
        yield PoseFrame(obs, img, 20.0, t, t)


def test_countdown_is_not_recorded_and_duration_is_respected() -> None:
    clf = CountingClassifier()
    cfg = TakeConfig(duration_s=4.0, countdown_s=2.0, frame_rate=12)
    phases: list[str] = []
    out = run_take(
        _frames(30.0, 20.0), cfg, {"m": clf}, filter_observations, FakeStore,
        on_frame=lambda f, phase, rem, rec: phases.append(phase),
    )
    assert out is not None and not out.aborted
    assert phases[0] == "countdown" and "recording" in phases
    assert 3.9 <= out.duration_s <= 4.1
    # 30 fps de entrada: o throttle de 1/12 s cai em 1 de cada 3 frames (10 fps efetivos)
    delivered = sum(f.delivered for f in out.recorder.frames)
    assert 38 <= delivered <= 44
    assert clf.calls == delivered


def test_empty_frames_are_recorded_and_reset_is_logged() -> None:
    cfg = TakeConfig(duration_s=2.0, countdown_s=0.0, frame_rate=12)
    clf = CountingClassifier()
    out = run_take(
        _frames(20.0, 5.0, with_person=lambda i: i == 0 or i % 3 != 0), cfg, {"m": clf},
        filter_observations, FakeStore,
    )
    assert out.recorder.resets            # lote vazio entregue => reset registrado
    assert set() in clf.cleanups


def test_abort_during_countdown_returns_none() -> None:
    cfg = TakeConfig(duration_s=2.0, countdown_s=5.0)
    out = run_take(_frames(10.0, 10.0), cfg, {}, filter_observations, FakeStore, should_stop=lambda: True)
    assert out is None


def test_marks_are_recorded_relative_to_first_frame() -> None:
    cfg = TakeConfig(duration_s=3.0, countdown_s=0.0)
    marks = [0]

    def on_frame(frame, phase, remaining, rec):
        if rec is not None and len(rec.frames) == 15:
            marks[0] = 1

    out = run_take(
        _frames(10.0, 6.0), cfg, {"m": CountingClassifier()}, filter_observations, FakeStore,
        on_frame=on_frame, pending_marks=lambda: marks[0],
    )
    assert len(out.recorder.marks) == 1 and out.recorder.marks[0] > 1.0


def test_finalize_writes_all_files_and_manifest(tmp_path: Path) -> None:
    cfg = TakeConfig(duration_s=4.0, countdown_s=0.0, frame_rate=12)
    out = run_take(_frames(15.0, 10.0), cfg, {"m": CountingClassifier()}, filter_observations, FakeStore)
    color, reasons, quality = finalize_take(
        out, captures_dir=tmp_path / "captures", manifest_path=tmp_path / "manifest.csv",
        scenario_id="sentando", scenario_label="ADL", take=1, session_id="s1",
        fingerprint={"yolo": "x"}, camera_fps_nominal=30.0, cfg=cfg,
    )
    d = tmp_path / "captures" / "sentando"
    names = {p.name for p in d.iterdir()}
    assert {"sentando_take01_p0.npy", "sentando_take01_p0_t.npy", "sentando_take01_raw.npz",
            "sentando_take01_decisions.csv", "sentando_take01_meta.json"} <= names
    meta = json.loads((d / "sentando_take01_meta.json").read_text(encoding="utf-8"))
    assert meta["fingerprint"] == {"yolo": "x"} and meta["verdict"]["color"] == color
    assert abs(quality["pose_fps"] - 15.0) < 0.5
    rows = read_entries(tmp_path / "manifest.csv")
    assert len(rows) == 1 and rows[0]["quality_verdict"] == color and rows[0]["scenario_label"] == "ADL"
