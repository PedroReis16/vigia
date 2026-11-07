"""recordings.csv — um registro por TOMADA gravada pelo gravador leve (sem keypoints)."""

from __future__ import annotations

import csv
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

FIELDNAMES = [
    "take_id", "scenario_id", "scenario_label", "take_number", "session_id", "recorded_at",
    "video_path", "frames_path", "capture_path", "n_frames", "duration_s", "measured_fps",
    "capture_verdict", "event_start_t", "event_end_t", "duration_mode", "operator_note",
]


@dataclass(frozen=True)
class Recording:
    take_id: str
    scenario_id: str
    scenario_label: str
    take_number: int
    session_id: str
    video_path: Path
    frames_path: Path
    capture_path: Path
    n_frames: int
    duration_s: float
    measured_fps: float
    capture_verdict: str
    event_start_t: float | None = None
    event_end_t: float | None = None
    duration_mode: str = "fixed"
    operator_note: str = ""
    recorded_at: str = ""

    def __post_init__(self) -> None:
        if not self.recorded_at:
            object.__setattr__(self, "recorded_at", datetime.now(timezone.utc).isoformat(timespec="seconds"))

    def to_row(self) -> dict[str, str]:
        return {k: ("" if v is None else str(v)) for k, v in asdict(self).items()}


def append_recording(path: Path, rec: Recording) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    new = not path.exists()
    with path.open("a", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDNAMES)
        if new:
            w.writeheader()
        w.writerow(rec.to_row())


def read_recordings(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def takes_recorded(path: Path, scenario_id: str) -> set[int]:
    return {int(r["take_number"]) for r in read_recordings(path) if r["scenario_id"] == scenario_id}
