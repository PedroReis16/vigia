"""
Worker para processamento assíncrono dos frames capturados
"""

from functools import lru_cache
import queue
from typing import Any
import numpy as np  # pyright: ignore[reportMissingImports]
from shared import get_settings
from capture.frame_processor import process_frame
from capture.models import SlidingWindowManager
from capture.features_processor import extract_features, normalize_features


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

        frame, capture_date = self.raw_frame_queue.get()

        if frame is None:
            return False

        # Processa o frame e obtém os resultados
        frame_result: dict[int, dict[str, Any]] = process_frame(frame, capture_date)
        self.raw_frame_queue.task_done()

        if not frame_result:
            return True

        ready_ids = self._slider_window_manager.update(frame_result)

        for person_id in ready_ids:
            window = self._slider_window_manager.get_window(person_id)
            if not window:
                continue

            try:
                features = extract_features(list(window))

                normalized_features = normalize_features(features)

                
            except Exception as error:
                print(
                    f"Erro ao extrair features person_id={person_id}: {error}",
                    flush=True,
                )

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
        try:
            self.raw_frame_queue.put_nowait(None)
        except queue.Full:
            # fila cheia: descarta um item e reinsere o sentinel
            try:
                self.raw_frame_queue.get_nowait()
            except queue.Empty:
                pass
            try:
                self.raw_frame_queue.put_nowait(None)
            except queue.Full:
                pass

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
