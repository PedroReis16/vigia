from functools import lru_cache
import queue
import numpy as np # type: ignore
import time

from shared import get_settings

class FrameQueue:
    """Worker para processamento assíncrono dos frames capturados"""

    def __init__(self, frame_rate: int) -> None:
        self._frame_rate = frame_rate
        self.frame_queue = queue.Queue(maxsize=30) #TODO: Colocar o tamanho dinamico da fila de acordo com o modelo de classificação
        self.last_classify = time.monotonic()

    def push(self, frame: np.ndarray) -> None:
        """
        Insere as coordenadas brutas do frame na fila
        A fila é processada conforme a taxa de frames definida nas configurações, caso não esteja disponível para inserção, os dados são descartados
        
        Args:
            frame: Frame capturado pelo YOLO
        Returns:
            None
        """

        if time.monotonic() - self.last_classify >= 1.0 / self._frame_rate:
            self.last_classify = time.monotonic()
            try:
                self.frame_queue.put_nowait(frame)
            except queue.Full:
                pass

@lru_cache
def get_frame_queue(frame_rate: int) -> FrameQueue:
    return FrameQueue(frame_rate)