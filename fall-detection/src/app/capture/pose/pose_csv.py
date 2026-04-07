"""Serialização de keypoints por frame em arquivos CSV (append com header na primeira linha)."""

from __future__ import annotations

import os

import pandas as pd

from app.capture.pose.person_data import PersonData


def _frame_rows(
    frame_data: list[PersonData], *, capture_seq: int
) -> list[dict[str, object]]:
    lines: list[dict[str, object]] = []
    for person in frame_data:
        for body_data in person.body_data:
            lines.append(
                {
                    "capture_seq": capture_seq,
                    "person_id": person.person_id,
                    "label": body_data.label,
                    "x": body_data.x,
                    "y": body_data.y,
                    "conf": body_data.conf,
                }
            )
    return lines


def append_pose_csv(path: str, frame_data: list[PersonData], *, capture_seq: int) -> None:
    lines = _frame_rows(frame_data, capture_seq=capture_seq)
    if not lines:
        return
    write_header = not os.path.isfile(path)
    df = pd.DataFrame(lines)
    df.to_csv(path, index=False, mode="w" if write_header else "a", header=write_header)
