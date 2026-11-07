from datetime import datetime
from pathlib import Path

from vigia_lab.manifest import (
    FIELDNAMES,
    ManifestEntry,
    append_entries,
    read_entries,
    takes_for_scenario,
)
from vigia_lab.takes import clip_id, new_session_id, next_take_number, takes_from_filenames


def test_next_take_starts_at_one_and_skips_gaps() -> None:
    assert next_take_number(set()) == 1
    assert next_take_number({1, 2, 5}) == 6


def test_takes_from_filenames_ignores_labels_and_time_files(tmp_path: Path) -> None:
    for name in [
        "x_take01_p0.npy", "x_take01_p0_labels.npy", "x_take01_p0_t.npy",
        "x_take03_p1.npy", "y_take09_p0.npy",
    ]:
        (tmp_path / name).touch()
    assert takes_from_filenames(tmp_path, "x") == {1, 3}
    assert takes_from_filenames(tmp_path / "nao_existe", "x") == set()


def test_ids() -> None:
    assert clip_id("sentando", 7, 1) == "sentando_take07_p1"
    assert new_session_id(datetime(2026, 9, 12, 14, 32, 5)) == "20260912_143205"


def _entry(take: int = 1, **kw) -> ManifestEntry:
    return ManifestEntry(
        clip_id=clip_id("sentando", take, 0), is_fall=False, src_fps=12.5,
        lbl_path=Path("a_labels.npy"), group_id="sentando_take01", px_path=Path("a.npy"),
        scenario_id="sentando", scenario_label="ADL", take_number=take, person_idx=0,
        n_frames=100, session_id="s", **kw,
    )


def test_manifest_roundtrip_has_old_and_new_columns(tmp_path: Path) -> None:
    path = tmp_path / "manifest.csv"
    append_entries(path, [_entry(1), _entry(2, event_t=4.2, quality_verdict="verde")])
    rows = read_entries(path)
    assert len(rows) == 2
    assert set(rows[0]) == set(FIELDNAMES)
    assert rows[1]["event_t"] == "4.2"
    assert rows[0]["event_t"] == ""
    assert takes_for_scenario(path, "sentando") == {1, 2}
