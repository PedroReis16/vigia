"""
Processa os frames capturados para inclusão na fila de processamento
"""

import numpy as np # pyright: ignore[reportMissingImports]

from capture.frame_worker import get_worker
from capture.models import get_yolo_model

def process_frame(frame: np.ndarray) -> None:
    """
    Processa o frame capturado para inclusão na fila de processamento
    """
    try:
        model = get_yolo_model()

        results = model.predict(frame, device="cpu", conf=0.75)

        if len(results) <= 0:
            return

        # print(results)
        
        get_worker().insert_slider_window(frame)

    except Exception as error:
        print(f"Erro ao processar o frame: {error}")