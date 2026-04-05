from app.config import Settings
from app.capture.io import FrameSaveWorker, StreamOutWorker, optional_stream_worker
from app.capture.loop import CaptureLoopContext, run_capture_loop
from app.capture.pose import PoseModel
import cv2
import os
import shutil

def run_capture(settings: Settings)-> None:
    """Executa o loop de captura de imagens da câmera."""
    
    pose_csv_dir: str | None = None
    if settings.data_path:
        if settings.pose_csv_window_seconds <= 0:
            raise ValueError("pose_csv_window_seconds must be greater than 0")
        print(f"Removing data path: {settings.data_path}")
        if os.path.isdir(settings.data_path):
            shutil.rmtree(settings.data_path)
        os.makedirs(settings.data_path, exist_ok=True)
        if settings.frames_dir:
            os.makedirs(settings.frames_dir, exist_ok=True)
        pose_csv_dir = settings.data_path

    stream: StreamOutWorker | None = None

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

    cap = cv2.VideoCapture(settings.video_capture_source)

    pose_model = PoseModel(model_path=settings.yolo_pose_model, device=settings.yolo_model_device)
    show_video = settings.show_video

    run_capture_loop(
        CaptureLoopContext(
            cap=cap,
            show_video=show_video,
            pose_model=pose_model,
            capture_per_second=settings.captures_per_second,
            pose_csv_dir=pose_csv_dir,
            pose_csv_window_seconds=settings.pose_csv_window_seconds,
            stream=stream,
            saver=saver,
        )
    )