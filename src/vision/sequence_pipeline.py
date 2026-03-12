"""Pipeline: lista de frames → YOLO → features → sequência (n_frames, n_features) para LSTM."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import numpy as np

from src.vision.yolo_features import (
    extract_features_from_results,
    features_per_frame_to_sequence,
)

if TYPE_CHECKING:
    from src.ml.yolo_detector import YOLODetector

logger = logging.getLogger(__name__)

# Chaves de features usadas na sequência (compatível com LSTM atual)
DEFAULT_SEQUENCE_KEYS = ("center_x", "center_y", "width", "height", "conf")


class SequencePipeline:
    """Converte uma lista de frames em array (n_frames, n_features) via YOLO e extração de features.

    Responsabilidade única: dado detector, frames e dimensões, retorna a sequência
    normalizada. Pode ser reutilizado e testado sem UI.
    """

    def __init__(
        self,
        detector: YOLODetector,
        *,
        imgsz: int = 640,
        conf: float = 0.7,
        device: str = "cpu",
        sequence_keys: tuple[str, ...] = DEFAULT_SEQUENCE_KEYS,
        max_detections_per_frame: int = 1,
    ) -> None:
        """Inicializa o pipeline.

        Args:
            detector: Detector YOLO (lazy load pelo detector).
            imgsz: Tamanho de entrada para YOLO.
            conf: Confiança mínima.
            device: Dispositivo ('cpu' ou 'cuda').
            sequence_keys: Chaves dos dicts de features na sequência.
            max_detections_per_frame: Máximo de detecções por frame (1 = pessoa principal).
        """
        self._detector = detector
        self._imgsz = imgsz
        self._conf = conf
        self._device = device
        self._sequence_keys = sequence_keys
        self._max_detections = max_detections_per_frame

    def build_sequence(
        self,
        frames: list[np.ndarray],
        frame_width: int,
        frame_height: int,
    ) -> np.ndarray | None:
        """Gera a sequência (n_frames, n_features) a partir dos frames.

        Args:
            frames: Lista de imagens BGR (OpenCV).
            frame_width: Largura do frame (para normalização).
            frame_height: Altura do frame (para normalização).

        Returns:
            Array (n_frames, n_features) ou None se frames vazios.
        """
        if not frames:
            return None

        features_per_frame: list[list[dict]] = []
        for frame in frames:
            results = self._detector.predict(
                source=frame,
                imgsz=self._imgsz,
                conf=self._conf,
                device=self._device,
                verbose=False,
            )
            feats = extract_features_from_results(
                results,
                frame_width=frame_width,
                frame_height=frame_height,
                normalize=True,
                max_detections=self._max_detections,
            )
            features_per_frame.append(feats)

        return features_per_frame_to_sequence(
            features_per_frame,
            keys=self._sequence_keys,
            pick_best=True,
        )
