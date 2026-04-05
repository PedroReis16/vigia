from __future__ import annotations
import os
import shutil
import time
from typing import Optional
import cv2
import numpy as np
import pandas as pd

from app.capture.frame_data import PersonData

from app.capture.disk_capture import DiskFrameCapture
from app.capture.workers import FrameSaveWorker, StreamOutWorker, optional_stream_worker
from app.config import Settings
from app.capture.pose_model import PoseModel


def _save_frame_data(frame_data: list[PersonData], data_path: str) -> None:
    lines = []

    for person in frame_data:
        for body_data in person.body_data:
            lines.append({
                "person_id": person.person_id,
                "label": body_data.label,
                "x": body_data.x,
                "y": body_data.y,
                "conf": body_data.conf
            })

    df = pd.DataFrame(lines)
    df.to_csv(data_path, index=False)

def _execute_role(
    cap: cv2.VideoCapture,
    show_video: bool, 
    pose_model: PoseModel, 
    capture_per_second: int,
    pose_csv_path: str | None,
    stream: Optional[StreamOutWorker], 
    saver: Optional[FrameSaveWorker]
    )-> None:
    
    try:
        if capture_per_second <= 0:
            raise ValueError("capture_per_second must be greater than 0")

        capture_interval = 1.0 / capture_per_second
        _last_auto_capture = time.monotonic()

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            now = time.monotonic()

            if now - _last_auto_capture >= capture_interval:
                person_data = pose_model.capture_frame(frame)
                if pose_csv_path is not None:
                    _save_frame_data(frame_data=person_data, data_path=pose_csv_path)
                print(f"Saved frame data for {len(person_data)} people")
                _last_auto_capture = now

            if stream is not None:
                stream.send_frame(frame)

            if show_video:
                frame = cv2.flip(frame, 1)
                cv2.imshow("Detection", frame)
                key = cv2.waitKey(1) & 0xFF
                if key == ord("q"):
                    break

    finally:
        cap.release()
        cv2.destroyAllWindows()
        if stream is not None:
            stream.stop()
        if saver is not None:
            saver.stop()



def run(settings: Settings) -> None:

    pose_csv_path: str | None = None
    if settings.data_path:
        print(f"Removing data path: {settings.data_path}")
        if os.path.isdir(settings.data_path):
            shutil.rmtree(settings.data_path)
        os.makedirs(settings.data_path, exist_ok=True)
        if settings.frames_dir:
            os.makedirs(settings.frames_dir, exist_ok=True)
        pose_csv_path = os.path.join(settings.data_path, "poses.csv")


    stream: Optional[StreamOutWorker] | None = None
    
    if settings.stream_video:
        stream = optional_stream_worker(
            settings.stream_ingest_url,
            settings.stream_ingest_token,
            settings.stream_target,
        )
        
    saver: FrameSaveWorker | None = None
    if settings.frames_dir:
        saver = FrameSaveWorker()
        saver.start()

    disk: DiskFrameCapture | None = None
    if settings.frames_dir:
        disk = DiskFrameCapture(settings.frames_dir, saver)

    cap = cv2.VideoCapture(settings.video_capture_source)

    pose_model = PoseModel(model_path=settings.yolo_pose_model, device=settings.yolo_model_device)
    show_video = settings.show_video

    _execute_role(
        cap=cap,
        show_video=show_video,
        pose_model=pose_model,
        capture_per_second=settings.captures_per_second,
        pose_csv_path=pose_csv_path,
        stream=stream,
        saver=saver
    )