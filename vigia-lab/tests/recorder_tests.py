import csv
import json
from pathlib import Path

import numpy as np

from core.models.types import FallDecision
from vigia_lab.recorder import FrameRecord, TakeRecorder, take_paths


def _kp(conf: float = 0.9, torso: bool = True) -> np.ndarray:
    k = np.zeros((17, 3), dtype=np.float32)
    k[:, :2] = 50.0
    k[:, 2] = conf
    if not torso:
        k[[5, 6, 11, 12], 2] = 0.0
    return k


def _frame(i: int, people: dict[int, np.ndarray], delivered: bool = True, t0: float = 100.0) -> FrameRecord:
    return FrameRecord(
        frame_idx=i, t_wall=t0 + i * 0.1, t_mono=i * 0.1, person_ids=list(people),
        keypoints=list(people.values()), delivered=delivered, yolo_ms=20.0, brightness=100.0,
        reset_all=not people,
    )


def test_ghost_track_without_torso_is_discarded_and_gaps_zero_filled(tmp_path: Path) -> None:
    rec = TakeRecorder()
    for i in range(12):
        people = {1: _kp(), 2: _kp(torso=False)}
        if i == 5:
            people = {2: _kp(torso=False)}      # pessoa 1 some neste frame
        rec.add_frame(_frame(i, people))

    clips = rec.save_clips(tmp_path, "sentando", 3, is_fall=False, min_frames=10)
    assert [c.clip_id for c in clips] == ["sentando_take03_p0"]
    kp = np.load(clips[0].px_path)
    assert kp.shape == (12, 17, 3)
    assert not kp[5].any()                      # ausência = zeros
    assert set(np.load(clips[0].lbl_path).tolist()) == {0}
    np.testing.assert_allclose(np.load(clips[0].t_path)[:3], [0.0, 0.1, 0.2])


def test_fall_label_is_two_and_low_conf_joints_are_zeroed(tmp_path: Path) -> None:
    rec = TakeRecorder()
    k = _kp()
    k[0, 2] = 0.2                               # abaixo de 0,3
    for i in range(10):
        rec.add_frame(_frame(i, {1: k}))
    clip = rec.save_clips(tmp_path, "queda_de_frente", 1, is_fall=True, min_frames=10)[0]
    assert set(np.load(clip.lbl_path).tolist()) == {2}
    assert not np.load(clip.px_path)[0, 0].any()


def test_raw_keeps_prefilter_keypoints_and_all_frames(tmp_path: Path) -> None:
    rec = TakeRecorder()
    k = _kp()
    k[0, 2] = 0.2
    rec.add_frame(_frame(0, {7: k}, delivered=False))
    rec.add_frame(_frame(1, {}, delivered=True))
    path = tmp_path / "raw.npz"
    rec.save_raw(path)
    z = np.load(path)
    assert z["keypoints"][0, 0, 0, 2] == np.float32(0.2)      # PRÉ-filtro preservado
    assert z["person_ids"][1, 0] == -1
    assert z["delivered"].tolist() == [False, True]
    assert len(rec.resets) == 1 and rec.resets[0]["frame_idx"] == 1


def test_decisions_csv_and_meta(tmp_path: Path) -> None:
    rec = TakeRecorder()
    rec.add_frame(_frame(0, {1: _kp()}))
    rec.add_decisions(0, 100.0, "gru34", [FallDecision(1, "FALL", True, {"probs": [0.2, 0.8]})], 1.5)
    rec.add_decisions(0, 100.0, "math", [FallDecision(1, "SUSPECT", False, {"score": 0.4})], 0.7)
    rec.mark_event(100.5)

    paths = take_paths(tmp_path, "x", 1)
    paths["dir"].mkdir()
    rec.save_decisions(paths["decisions"], "x_take01")
    rows = list(csv.DictReader(paths["decisions"].open(encoding="utf-8")))
    assert rows[0]["model"] == "gru34" and rows[0]["prob_fall"] == "0.8" and rows[0]["alert"] == "1"
    assert rows[1]["score"] == "0.4"

    rec.save_meta(paths["meta"], {"a": 1})
    meta = json.loads(paths["meta"].read_text(encoding="utf-8"))
    assert meta["marks_t_rel"] == [0.5]


def test_id_stats_counts_delivered_id_changes_and_fallback_zero() -> None:
    rec = TakeRecorder()
    k = _kp()
    ids_per_frame = [{1: k}, {1: k}, {0: k}, {1: k}]     # 0 = ID de reserva do vigia
    for i, people in enumerate(ids_per_frame):
        rec.add_frame(_frame(i, people, delivered=True))
    stats = rec.id_stats()
    assert stats == {"id_set_changes_delivered": 2, "id_fallback_frames": 1, "untracked_frames": 0}


def test_id_stats_ignores_people_who_just_leave_or_enter() -> None:
    rec = TakeRecorder()
    k = _kp()
    seq = [{1: k, 2: k}, {1: k, 2: k}, {1: k}, {1: k, 3: k}, {3: k}]   # 2 sai; 3 entra; 1 sai
    for i, people in enumerate(seq):
        rec.add_frame(_frame(i, people, delivered=True))
    # só a transição {1,3} -> {3} NÃO é troca; {1} -> {1,3} entrada pura; nenhuma troca (sai OU entra)
    assert rec.id_stats()["id_set_changes_delivered"] == 0
    rec2 = TakeRecorder()
    for i, people in enumerate([{1: k}, {2: k}]):                         # 1 foi trocado por 2
        rec2.add_frame(_frame(i, people, delivered=True))
    assert rec2.id_stats()["id_set_changes_delivered"] == 1
