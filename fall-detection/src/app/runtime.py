from __future__ import annotations
import shutil
import time
from typing import Optional
import cv2
from concurrent.futures import ThreadPoolExecutor, Future
from ultralytics import YOLO
from app.capture.disk_capture import DiskFrameCapture
from app.capture.roi import central_roi
from app.capture.workers import FrameSaveWorker, StreamOutWorker, optional_stream_worker
from app.config import Settings

def run(settings: Settings) -> None:

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

    try:
        if settings.data_path:
            print(f"Removing data path: {settings.data_path}")
            shutil.rmtree(settings.data_path)

        detect_model = YOLO(settings.yolo_model)
        pose_model = YOLO(settings.yolo_pose_model)

        detect_classes = list(range(1, 80))

        def run_pose(f):
            return pose_model.predict(f, conf=0.75, verbose=False, device=settings.yolo_model_device)

        def run_detect(f):
            return detect_model.predict(f, conf=0.75, verbose=False, classes=detect_classes, device=settings.yolo_model_device)

        with ThreadPoolExecutor(max_workers=2) as executor:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                # Submete os dois modelos simultaneamente
                fut_pose = executor.submit(run_pose, frame)
                fut_detect = executor.submit(run_detect, frame)

                # Aguarda os dois terminarem
                pose_results = fut_pose.result()
                detect_results = fut_detect.result()

                annotated_frame = pose_results[0].plot(img=frame.copy())
                annotated_frame = detect_results[0].plot(img=annotated_frame.copy())

                if stream is not None:
                    stream.send_frame(annotated_frame)

                if settings.show_video:
                    cv2.imshow("Detection", annotated_frame)
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