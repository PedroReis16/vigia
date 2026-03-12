"""Configuração do preview (câmera/vídeo) e da captura de sequências para LSTM."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import numpy as np


@dataclass(frozen=True)
class PreviewConfig:
    """Opções de exibição e captura de sequências.

    Agrupa todas as configurações que hoje eram passadas ao WebcamPreviewService,
    permitindo injeção única e testes mais simples.
    """

    # Fonte de frames
    camera_index: int | list[int] = 0
    video_source: str | Path | None = None

    # Janela e exibição
    window_name: str = "older-fall webcam"
    flip_horizontal: bool = False

    # YOLO
    yolo_model_path: str = "yolov8s.pt"
    detection_conf: float = 0.7
    detection_imgsz: int = 640

    # Captura (manual e contínua)
    frames_to_capture: int = 30
    capture_output_dir: str | Path = "data/captures"
    save_frames: bool = False
    capture_key: int = ord("c")
    continuous_capture: bool = False
    capture_interval_frames: int = 1
    on_sequence_ready: Callable[[np.ndarray], None] | None = None
    save_continuous_sequences: bool = False

    @property
    def camera_indices(self) -> list[int]:
        """Lista de índices de câmera para fallback."""
        idx = self.camera_index
        return [idx] if isinstance(idx, int) else list(idx)

    @property
    def is_debug_video(self) -> bool:
        """True quando a fonte é um arquivo de vídeo (modo debug)."""
        return self.video_source is not None

    @property
    def capture_output_path(self) -> Path:
        """Diretório de saída como Path."""
        return Path(self.capture_output_dir)

    @property
    def effective_frames_to_capture(self) -> int:
        """Número de frames por janela (>= 1)."""
        return max(1, self.frames_to_capture)

    @property
    def effective_capture_interval(self) -> int:
        """Intervalo de frames no modo contínuo (>= 1)."""
        return max(1, self.capture_interval_frames)
