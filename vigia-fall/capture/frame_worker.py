"""
Worker para processamento assíncrono dos frames capturados
"""

from functools import lru_cache
import queue
import time
from typing import Any
import numpy as np  # pyright: ignore[reportMissingImports]
from shared import get_settings
from capture.frame_processor import process_frame
from capture.models import SlidingWindowManager
from capture.features_processor import extract_features

from shared.models import COORDINATES_CONSTANTS


class FrameWorker:
    """
    Worker para processamento assíncrono dos frames capturados
    """

    def __init__(self, frame_rate: int, slider_window_size: int) -> None:
        """
        Inicializa o worker
        """
        self.raw_frame_queue = queue.Queue(maxsize=frame_rate)
        self._slider_window_manager = SlidingWindowManager(
            window_size=slider_window_size
        )

    def __consume_raw_frame(self) -> bool:
        """
        Consome um frame da fila de frames brutos
        """

        # TODO: Reabilitar o consumo real de frames para testes reais
        frame, capture_date = self.raw_frame_queue.get()

        if frame is None:
            return False

        # Processa o frame e obtém os resultados
        frame_result: dict[int, dict[str, Any]] = process_frame(frame, capture_date)
        self.raw_frame_queue.task_done()

        if not frame_result:
            return True

        ready_ids = self._slider_window_manager.update(frame_result)

        ready_ids = [1]

        for person_id in ready_ids:
            # TODO: Reabilitar o consumo real de frames para testes reais
            window = self._slider_window_manager.get_window(person_id)
            extract_features(person_id, list(window))

            # extract_features(person_id, COORDINATES_CONSTANTS)

        # time.sleep(1)

        return True

    def run(self) -> None:
        """
        Executa o worker
        """

        while True:
            if not self.__consume_raw_frame():
                break  # sai do loop se a fila de frames brutos estiver vazia

    def stop(self) -> None:
        """
        Para o worker
        """
        self.raw_frame_queue.put_nowait(None)  # put a sentinel value to stop the worker

    def insert_raw_frame(self, frame: np.ndarray, capture_date: float) -> None:
        """
        Insere um frame na fila de processamento
        """

        try:
            self.raw_frame_queue.put_nowait((frame, capture_date))
        except queue.Full:
            try:
                self.raw_frame_queue.get_nowait()  # descarta o mais antigo
            except queue.Empty:
                pass
            self.raw_frame_queue.put_nowait((frame, capture_date))


@lru_cache
def get_worker() -> FrameWorker:
    """
    Retorna o worker de processamento de frames
    """
    settings = get_settings()
    return FrameWorker(settings.frame_rate, settings.slider_window_size)
