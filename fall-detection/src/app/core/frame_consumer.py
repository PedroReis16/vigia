"""Consumo de frames publicados pelo loop de captura (ZMQ SUB)."""

from __future__ import annotations

from multiprocessing import Queue
from collections import defaultdict, deque
import multiprocessing
import pickle

import numpy as np
import zmq
import time
from ultralytics import YOLO

from app.config.ipc import configure_frame_sub_socket
from app.logging import get_logger
from queue import Queue

logger = get_logger("frame_consumer")

WINDOW_SIZE = 30
GRU_INTERVAL = 1.0
NUM_KEYPOINTS = 17


def _capture_frame(pose_model: YOLO, frame: np.ndarray) -> list[tuple[int, np.ndarray]] | None:
    """ 
    Retorna lista de (person_id, kpts_flat) onde kpts_flat é shape (51,).
    Keypoints com conf < 0.25 são zerados (mantém posição fixa no vetor).
    """
    
    results = pose_model.track(
        frame, conf=0.25, verbose=False,
        device="cpu", persist=True, tracker="botsort.yaml",
    )
    frame_results = []

    for result in results:
        kpts = result.keypoints

        if kpts is None or kpts.data is None or len(kpts.data) == 0:
            continue

        boxes = result.boxes
        ids_tensor = getattr(boxes, "id", None)
        person_ids = (
            [int(ids_tensor[i].item()) for i in range(len(kpts.data))]
            if ids_tensor is not None and len(ids_tensor) >= len(kpts.data)
            else list(range(len(kpts.data)))
        )

        for person_id, person_kpts in zip(person_ids, kpts.data):
            kpts_np = person_kpts.numpy()

            # Zera keypoints com confiança baixa
            mask = kpts_np[:, 2] < 0.25
            kpts_np[mask] = 0.0

            frame_results.append((person_id, kpts_np.flatten()))

    return frame_results


def _feed_buffers(
    detections: list[tuple[int, np.ndarray]],
    buffers: dict[int, deque],
    last_inference: dict[int, float],
    last_seen: dict[int, float],
    buffer_queue: Queue,
    now: float
) -> None:
    """
    Alimenta as janelas deslizantes, preparando os dados para o processo de classificação.
    """

    # Capta o ID das pessoas ativas na cena a partir das detecções
    active_person_ids = {pid for pid, _ in detections}

    for person_id, kpts_flat in detections:
        last_seen[person_id] = now

        #deque(maxlen=30) desliza automaticamente ao atingir capacidade 
        buffers[person_id].append(kpts_flat)

        is_full_window = len(buffers[person_id]) == WINDOW_SIZE
        is_old = (now - last_inference.get(person_id, 0.0)) >= GRU_INTERVAL

        if is_full_window and is_old:
            window = np.array(buffers[person_id])

            try:
                buffer_queue.put_nowait((person_id, window))
            except multiprocessing.queues.Full:
                logger.warning(f"Buffer de processamento cheio, descartando janela do ID '{person_id}'")

    # Remove buffers de pessoas ausentes nas cenas
    for pid in list(buffers.keys()):
        if pid not in active_person_ids and (now - last_seen.get(pid, now)) >= 3.0:
            del buffers[pid]
            last_inference.pop(pid, None)
            last_seen.pop(pid, None)
            logger.debug(f"buffer do ID '{pid}' removido por inatividade")



   

def run_frame_consumer(
    pose_model: YOLO, captures_per_second: int, buffer_queue: Queue
) -> None:
    """Consome frames da câmera e captura keypoints das pessoas."""

    buffers = defaultdict[int, deque](lambda: deque(maxlen=WINDOW_SIZE))
    last_inference: dict[int, float] = {}
    last_seen: dict[int, float] = {}

    context = zmq.Context()
    socket = context.socket(zmq.SUB)
    configure_frame_sub_socket(socket)

    capture_interval = 1.0 / captures_per_second

    try:
        last_capture = time.monotonic()

        while True:
            # Recebe o frame do socket (vindo do App.Capture)
            _, payload = socket.recv_multipart()
            frame = pickle.loads(payload)
            frame = np.array(frame)

            now = time.monotonic()

            # Verifica se o frame esta dentro do intervalo de leitura por segundo (ex: 10fps)
            if now - last_capture < capture_interval:
                continue

            last_capture = now

            # Captura os keypoints das pessoas no frame
            results = _capture_frame(pose_model, frame)
            if not results:
                continue

            _feed_buffers(results, buffers, last_inference, last_seen, buffer_queue,now)
    except KeyboardInterrupt:
        pass
    except Exception as e:
        logger.error("erro ao consumir frames: {}", e)
    finally:
        socket.close()
        context.term()
