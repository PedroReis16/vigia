"""Loop do worker em thread: consome fila de `PoseProcessJob`."""

from __future__ import annotations

import os
import queue
from typing import Any

import cv2

from app.capture.pose.pose_csv import append_pose_csv
from app.capture.pose.pose_model import PoseModel
from app.capture.pose.pose_process_job import PoseProcessJob


def _frame_snapshot_path_for_csv(csv_path: str) -> str:
    """CSV em ``…/coordinates/poses_N.csv`` → PNG em ``…/frames/poses_N.png``."""
    coord_dir = os.path.dirname(csv_path)
    data_root = os.path.dirname(coord_dir)
    stem, _ = os.path.splitext(os.path.basename(csv_path))
    return os.path.join(data_root, "frames", f"{stem}.png")


def _write_segment_last_frame_snapshot(csv_path: str, frame: Any) -> None:
    """Grava PNG com o mesmo basename do CSV, na subpasta ``frames``."""
    out_path = _frame_snapshot_path_for_csv(csv_path)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    cv2.imwrite(out_path, frame)


def pose_worker_loop(pose_model: PoseModel, work_q: "queue.Queue[PoseProcessJob | None]") -> None:
    prev_csv_path: str | None = None
    last_frame_for_segment: Any | None = None

    while True:
        job = work_q.get()
        if job is None:
            if prev_csv_path is not None and last_frame_for_segment is not None:
                _write_segment_last_frame_snapshot(prev_csv_path, last_frame_for_segment)
            work_q.task_done()
            break
        try:
            if job.csv_path is not None:
                if prev_csv_path is not None and job.csv_path != prev_csv_path:
                    if last_frame_for_segment is not None:
                        _write_segment_last_frame_snapshot(prev_csv_path, last_frame_for_segment)

            person_data = pose_model.capture_frame(job.frame)
            if job.csv_path is not None:
                append_pose_csv(job.csv_path, person_data, capture_seq=job.capture_seq)
                prev_csv_path = job.csv_path
                last_frame_for_segment = job.frame
        finally:
            work_q.task_done()
