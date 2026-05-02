"""Loop contínuo: leitura da câmera, enfileiramento de pose/CSV, stream e preview."""

from __future__ import annotations

import os
from pathlib import Path
import queue
import threading
import time

import cv2
import zmq
import pickle

from app.capture.loop.capture_loop_context import CaptureLoopContext
from app.capture.pose.pose_process_job import PoseProcessJob
from app.capture.pose.pose_worker import pose_worker_loop
from app.fiware.posture_notifier import FiwarePostureNotifier
from app.logging import get_logger

from app.capture.fall_classifier import FallClassifier, build_keypoints_list
from app.streaming.stream_video import stream_video

logger = get_logger("capture")

def disparar_alerta() -> None:
    """Dispara o alerta de queda."""
    logger.warning("alerta de queda disparado")

def run_capture_loop(ctx: CaptureLoopContext) -> None:
    """Loop contínuo: leitura da câmera, enfileiramento de pose/CSV, stream e preview."""

    pose_work_q: queue.Queue[PoseProcessJob | None] | None = None
    pose_worker: threading.Thread | None = None
    try:
        if ctx.capture_per_second <= 0:
            raise ValueError("capture_per_second must be greater than 0")

        capture_interval = 1.0 / ctx.capture_per_second
        _last_auto_capture = time.monotonic()
        _csv_segment_start: float | None = None
        _csv_segment_index = 0
        _pose_capture_seq = 0

        # Fila acoplada: se o worker atrasar, a captura espera em put() (evita fila infinita).
        pose_work_q = queue.Queue(maxsize=4)
        pose_worker = threading.Thread(
            target=pose_worker_loop,
            args=(ctx.pose_model, pose_work_q),
            name="pose-csv-worker",
            daemon=True,
        )
        pose_worker.start()

        clf = FallClassifier(Path(__file__).resolve().parents[4]/"model"/"classifier_svm.onnx")
        posture_notifier = FiwarePostureNotifier()
        last_posture_state: str | None = None

        first_infer = True

        context = zmq.Context()
        socket = context.socket(zmq.PUB)
        socket.bind("ipc:///tmp/frames.ipc")
        time.sleep(0.5)

        while True:
            ret, frame = ctx.cap.read()
            if not ret:
                break

            if first_infer:
                logger.info(
                    "primeira inferência de pose (CPU pode demorar dezenas de segundos)…"
                )
                first_infer = False

            payload = pickle.dumps(frame, protocol=pickle.HIGHEST_PROTOCOL)
            socket.send_multipart([b"frame", payload])

            # result = ctx.pose_model.model(frame, verbose=False)[0]
            # annotated = result.plot()

            # if result.keypoints is not None and len(result.keypoints) > 0:
            #     # Converte saída do YOLO para o formato do classificador
            #     kps = result.keypoints.xy.cpu().numpy()  # (N_pessoas, 17, 2)
            #     kconf = result.keypoints.conf.cpu().numpy()
            #     keypoints = build_keypoints_list(kps, kconf, person_idx=0)
            #     result = clf.predict(keypoints)

            #     if result is not None:
            #         logger.debug("resultado classificador: {}", result)
            #         posture_state = str(result.get("label") or "").strip()
            #         if posture_state and posture_state != last_posture_state:
            #             last_posture_state = posture_state
            #             posture_notifier.notify_posture_changed(posture_state)

            # if ctx.stream is not None:
            #     ctx.stream.send_frame(annotated)

            if ctx.show_video:
                display = cv2.flip(frame, 1)
                cv2.imshow("Detection", display)
                key = cv2.waitKey(1) & 0xFF
                if key == ord("q"):
                    break

    finally:
        if pose_work_q is not None:
            pose_work_q.put(None)
        if pose_worker is not None:
            pose_worker.join(timeout=120.0)
        ctx.cap.release()
        cv2.destroyAllWindows()
        if ctx.stream is not None:
            ctx.stream.stop()
        if ctx.saver is not None:
            ctx.saver.stop()
        socket.close()
        context.term()