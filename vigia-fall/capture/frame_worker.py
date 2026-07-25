"""
Worker para processamento assíncrono dos frames capturados
"""

from functools import lru_cache
import queue
import numpy as np  # pyright: ignore[reportMissingImports]
from shared import get_settings


class FrameWorker: 
    """
    Worker para processamento assíncrono dos frames capturados
    """
    def __init__(self, frame_rate: int, slider_window_size: int) -> None:
        """
        Inicializa o worker
        """
        self.raw_frame_queue = queue.Queue(maxsize=frame_rate)
        self.slider_window_queue = queue.Queue(maxsize=slider_window_size)

    def __consume_raw_frame(self) -> bool:
        """
        Consome um frame da fila de frames brutos
        """
        from capture.frame_processor import process_frame
        
        frame = self.raw_frame_queue.get()

        if frame is None:
            return False

        process_frame(frame)
        self.raw_frame_queue.task_done()
        return True

    def __consume_slider_window(self) -> bool:
        """
        Inicializa o processamento da janela deslizante
        """
        pass

    def run(self) -> None:
        """
        Executa o worker
        """

        while True:
            if not self.__consume_raw_frame():
                break # sai do loop se a fila de frames brutos estiver vazia

            if not self.slider_window_queue.full():
                continue # continua o loop se a fila de janelas deslizantes não estiver cheia para iniciar o processamento

            self.__consume_slider_window()


    def stop(self) -> None:
        """
        Para o worker
        """
        self.raw_frame_queue.put_nowait(None) # put a sentinel value to stop the worker
        self.slider_window_queue.put_nowait(None) # put a sentinel value to stop the worker


    def insert_raw_frame(self, frame: np.ndarray) -> None:
        """
        Insere um frame na fila de processamento
        """

        try:
            self.raw_frame_queue.put_nowait(frame)
        except queue.Full:
            try:
                self.raw_frame_queue.get_nowait() # descarta o mais antigo
            except queue.Empty:
                pass
            self.raw_frame_queue.put_nowait(frame)


    def insert_slider_window(self, window: np.ndarray) -> None:
        """
        Insere uma janela na fila de processamento
        """
        try:
            self.slider_window_queue.put_nowait(window)
        except queue.Full:
            try:
                self.slider_window_queue.get_nowait() # descarta o mais antigo
            except queue.Empty:
                pass
            self.slider_window_queue.put_nowait(window)


@lru_cache
def get_worker() -> FrameWorker:
    """
    Retorna o worker de processamento de frames
    """
    settings = get_settings()
    return FrameWorker(settings.frame_rate, settings.slider_window_size)