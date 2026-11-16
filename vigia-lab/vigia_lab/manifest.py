"""manifest.csv append-only — um registro por clipe (pessoa) gravado.

Superconjunto das colunas do `keypoint_extraction`, para os scripts de
análise existentes continuarem lendo por nome.
"""

from __future__ import annotations

import csv
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

SOURCE_NAME = "vigia-lab"

FIELDNAMES = [
    "clip_id", "source", "is_fall", "src_fps", "lbl_path", "group_id", "px_path",
    "scenario_id", "scenario_label", "take_number", "person_idx", "n_frames",
    "session_id", "recorded_at", "operator_note",
    # novas no vigia-lab
    "event_t", "video_path", "quality_verdict", "meta_path",
]


@dataclass(frozen=True)
class ManifestEntry:
    clip_id: str
    is_fall: bool
    src_fps: float
    lbl_path: Path
    group_id: str
    px_path: Path
    scenario_id: str
    scenario_label: str
    take_number: int
    person_idx: int
    n_frames: int
    session_id: str
    operator_note: str = ""
    source: str = SOURCE_NAME
    recorded_at: str = ""
    event_t: float | None = None
    video_path: Path | None = None
    quality_verdict: str = ""
    meta_path: Path | None = None

    def __post_init__(self) -> None:
        if not self.recorded_at:
            object.__setattr__(
                self, "recorded_at",
                datetime.now(timezone.utc).isoformat(timespec="seconds"),
            )

    def to_row(self) -> dict[str, str]:
        return {k: ("" if v is None else str(v)) for k, v in asdict(self).items()}


def ensure_manifest(path: Path) -> None:
    if path.exists():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        csv.DictWriter(fh, fieldnames=FIELDNAMES).writeheader()


def append_entries(path: Path, entries: list[ManifestEntry]) -> None:
    ensure_manifest(path)
    with path.open("a", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDNAMES)
        for entry in entries:
            writer.writerow(entry.to_row())


def read_entries(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def takes_for_scenario(path: Path, scenario_id: str) -> set[int]:
    return {
        int(row["take_number"])
        for row in read_entries(path)
        if row["scenario_id"] == scenario_id
    }
