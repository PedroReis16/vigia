"""Loop do worker em thread: consome fila de `PoseProcessJob`."""

from __future__ import annotations

import queue

from app.capture.pose.pose_csv import append_pose_csv
from app.capture.pose.pose_model import PoseModel
from app.capture.pose.pose_process_job import PoseProcessJob


def pose_worker_loop(pose_model: PoseModel, work_q: "queue.Queue[PoseProcessJob | None]") -> None:
    while True:
        job = work_q.get()
        if job is None:
            work_q.task_done()
            break
        try:
            person_data = pose_model.capture_frame(job.frame)
            if job.csv_path is not None:
                append_pose_csv(job.csv_path, person_data, capture_seq=job.capture_seq)
        finally:
            work_q.task_done()
