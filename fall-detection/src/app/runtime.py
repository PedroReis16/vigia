from __future__ import annotations
import shutil
import time
from typing import Optional
import cv2
import numpy as np

from app.capture.disk_capture import DiskFrameCapture
from app.capture.workers import FrameSaveWorker, StreamOutWorker, optional_stream_worker
from app.config import Settings
from app.ml.pose_model import PoseModel

_prev_keypoints: tuple[float, float] | None = None


def _capture_frame(pose_model: PoseModel, frame: np.ndarray) -> None:
    global _prev_keypoints

    results = pose_model.predict(frame)

    for result in results:
        kpts = result.keypoints.data

        for person in kpts:
            x, y, conf = person[0]  # Ex.: nariz (keypoint 0)

            if conf < 0.75:
                continue

            cx, cy = float(x.item()), float(y.item())
            current_pos = (cx, cy)

            if _prev_keypoints is not None:
                px, py = _prev_keypoints
                distance = ((px - cx) ** 2 + (py - cy) ** 2) ** 0.5
                velocity = distance
                print(f"Deslocamento: {distance:.2f}px | Velocidade: {velocity:.2f}px/frame")

            _prev_keypoints = current_pos


def _execute_role(
    cap: cv2.VideoCapture,
    show_video: bool, 
    pose_model: PoseModel, 
    capture_per_second: int,
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
                _capture_frame(pose_model, frame)
                _last_auto_capture = now

            if stream is not None:
                stream.send_frame(frame)

            if show_video:
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

    if settings.data_path:
        print(f"Removing data path: {settings.data_path}")
        shutil.rmtree(settings.data_path)


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
        stream=stream,
        saver=saver
    )