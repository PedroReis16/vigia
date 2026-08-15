"""
Worker para processamento assíncrono dos frames capturados
"""

from collections import defaultdict, deque
from functools import lru_cache
import queue
from typing import Any
import numpy as np  # pyright: ignore[reportMissingImports]
from shared import get_settings
from capture.frame_processor import process_frame

# --- PIPELINE PEDRO (comentado para integração GRU) ---
# from capture.models import FallState, SlidingWindowManager, compute_fall_score, get_person_runtime_store
# from capture.features_processor import extract_features, normalize_features
# -------------------------------------------------------

from capture.models.gru_classifier import GRUFallClassifier
from integration.fiware_runner import notify_fall

GRU_WINDOW_SIZE = 20
GRU_INTERVAL = 0.5  # segundos entre inferências por pessoa


class FrameWorker:
    """
    Worker para processamento assíncrono dos frames capturados
    """

    def __init__(self, frame_rate: int, slider_window_size: int) -> None:
        """
        Inicializa o worker
        """
        self.raw_frame_queue = queue.Queue(maxsize=frame_rate)
        # --- PIPELINE PEDRO (comentado para integração GRU) ---
        # self._slider_window_manager = SlidingWindowManager(window_size=slider_window_size)
        # -------------------------------------------------------
        self._gru_classifier = GRUFallClassifier()
        self._gru_buffers: dict = defaultdict(lambda: deque(maxlen=GRU_WINDOW_SIZE))
        self._gru_last_inference: dict[int, float] = {}

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

        # --- PIPELINE PEDRO (comentado para integração GRU) ---
        # ready_ids = self._slider_window_manager.update(frame_result)
        # weights = {
        #     "trunk_angle_delta": 0.25,
        #     "trunk_angle_trend_r2": 0.20,
        #     "pca_ratio_delta": 0.15,
        #     "center_mass_max_accel_y": 0.20,
        #     "center_mass_accel_poly": 0.10,
        #     "trunk_angle_max_rate": 0.10,
        # }
        # for person_id in ready_ids:
        #     window = self._slider_window_manager.get_window(person_id)
        #     if not window:
        #         continue
        #     try:
        #         features = extract_features(list(window))
        #         normalized_features = normalize_features(features)
        #         score = compute_fall_score(normalized_features, weights)
        #         person_state = get_person_runtime_store().get_or_create(person_id)
        #         state = person_state.fall_detector.update(score, capture_date)
        #         if state == FallState.SUSPECT:
        #             pass
        #     except Exception as error:
        #         print(f"Erro ao extrair features person_id={person_id}: {error}", flush=True)
        # -------------------------------------------------------

        for person_id, data in frame_result.items():
            self._gru_buffers[person_id].append(data["raw_kpts"])
            elapsed = capture_date - self._gru_last_inference.get(person_id, 0)
            if (
                len(self._gru_buffers[person_id]) == GRU_WINDOW_SIZE
                and elapsed >= GRU_INTERVAL
            ):
                window = np.array(list(self._gru_buffers[person_id]))  # (20, 51)
                pred = self._gru_classifier.predict(window, person_id)
                self._gru_last_inference[person_id] = capture_date
                if pred is not None:
                    print(
                        f"[GRU] Pessoa {person_id}: {pred['label']}  FALL={pred['probs'][1]:.2f}",
                        flush=True,
                    )
                    if pred["alert"]:
                        try:
                            notify_fall(pred["label"])
                        except Exception as e:
                            print(f"[GRU] Falha FIWARE: {e}", flush=True)

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
