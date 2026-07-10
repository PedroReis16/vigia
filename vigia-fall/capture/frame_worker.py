"""
Worker para processamento assíncrono dos frames capturados
"""

import queue
import numpy as np  # pyright: ignore[reportMissingImports]

from capture.frame_processor import process_frame

class FrameWorker: 
    """
    Worker para processamento assíncrono dos frames capturados
    """
    def __init__(self, frame_rate: int) -> None:
        """
        Inicializa o worker
        """
        self.frame_queue = queue.Queue(maxsize=frame_rate)

    def run(self) -> None:
        """
        Executa o worker
        """

        while True:
            frame = self.frame_queue.get()

            if frame is None:
                break
            process_frame(frame)
            self.frame_queue.task_done()

    def stop(self) -> None:
        """
        Para o worker
        """
        self.frame_queue.put_nowait(None) # put a sentinel value to stop the worker


    def insert(self, frame: np.ndarray) -> None:
        """
        Insere um frame na fila de processamento
        """

        try:
            self.frame_queue.put_nowait(frame)
        except queue.Full:
            try:
                self.frame_queue.get_nowait() # descarta o mais antigo
            except queue.Empty:
                pass
            self.frame_queue.put_nowait(frame)