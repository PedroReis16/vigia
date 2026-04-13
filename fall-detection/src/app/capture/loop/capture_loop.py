"""Loop contínuo: leitura da câmera, enfileiramento de pose/CSV, stream e preview."""

from __future__ import annotations

import os
from pathlib import Path
import queue
import threading
import time

import cv2

from app.capture.loop.capture_loop_context import CaptureLoopContext
from app.capture.pose.pose_process_job import PoseProcessJob
from app.capture.pose.pose_worker import pose_worker_loop

from app.capture.fall_classifier import FallClassifier, build_keypoints_list

def disparar_alerta() -> None:
    """Dispara o alerta de queda."""
    print("Alerta de queda disparado")

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

        first_infer = True
        while True:
            ret, frame = ctx.cap.read()
            if not ret:
                break

            if first_infer:
                print(
                    "Primeira inferência de pose (CPU pode demorar dezenas de segundos)…",
                    flush=True,
                )
                first_infer = False

            results = ctx.pose_model.model(frame, verbose=False)[0]
            annotated = results.plot()

            if results.keypoints is not None and len(results.keypoints) > 0:
                # Converte saída do YOLO para o formato do classificador
                kps = results.keypoints.xy.cpu().numpy()  # (N_pessoas, 17, 2)
                kconf = results.keypoints.conf.cpu().numpy()
                keypoints = build_keypoints_list(kps, kconf, person_idx=0)
                resultado = clf.predict(keypoints)

                if resultado is None:
                    print("Sem resultados")
                else:
                    print(resultado)

            if ctx.stream is not None:
                ctx.stream.send_frame(annotated)

            if ctx.show_video:
                display = cv2.flip(annotated, 1)
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
