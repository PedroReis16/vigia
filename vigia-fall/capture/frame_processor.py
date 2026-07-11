"""
Processa os frames capturados para inclusão na fila de processamento
"""

import numpy as np # pyright: ignore[reportMissingImports]

from capture.frame_worker import get_worker
from capture.models import get_yolo_model,apply_kalman, cleanup_stale_trackers

def process_frame(frame: np.ndarray, capture_date: float) -> None:
    """
    Processa o frame capturado para inclusão na fila de processamento
    """
    try:
        model = get_yolo_model()

        results = model.track(
            frame, device="cpu", conf=0.25, verbose=False, persist=True, 
            tracker="botsort.yaml",classes=[0]) # 0 = pessoa

        if len(results) <= 0:
            return

        frame_results = []
        active_ids = []

        for result in results:
            kpts = result.keypoints

            if kpts is None or kpts.data is None or len(kpts.data) <= 0:
                continue

            boxes = result.boxes
            ids_tensor = getattr(boxes, "id", None)

            person_ids = (
                [int(ids_tensor[i].item()) for i in range(len(kpts.data))]
                if ids_tensor is not None and len(ids_tensor) >= len(kpts.data)
                else list(range(len(kpts.data)))
            )

            points= {}

            for person_id, person_kpts in zip(person_ids, kpts.data):
                kpts_np = person_kpts.numpy()

                points = {idx: valor.tolist() for idx, valor in enumerate(kpts_np) if valor[2] != 0.0} 

                # Aplicação do filtro de Kalman para suavização das posições
                smoothed_points = apply_kalman(person_id, capture_date, points)
                active_ids.append(person_id)
                frame_results.append((person_id,points, smoothed_points))

        # Remoção de trackers inativos
        cleanup_stale_trackers(set(active_ids))

        # Smoothed points que irá preencher a janela deslizante depois de ser aplicado a normalização das posições
        print(frame_results)

            

    except Exception as error:
        print(f"Erro ao processar o frame: {error}")