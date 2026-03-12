"""Controle de captura: buffers manual/contínuo e geração de overlays para exibição."""

from __future__ import annotations

import logging
from collections import deque
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import numpy as np

from src.vision.preview_config import PreviewConfig

logger = logging.getLogger(__name__)


@dataclass
class CaptureResult:
    """Resultado de uma captura pronta para processamento (YOLO + save/callback)."""

    frames: list[np.ndarray]
    frame_width: int
    frame_height: int
    is_continuous: bool
    continuous_window_index: int | None = None
    manual_save_frames: bool = False


@dataclass
class OverlayLine:
    """Uma linha de texto para desenhar no frame."""

    text: str
    position: tuple[int, int]
    color: tuple[int, int, int] = (0, 255, 0)
    font_scale: float = 0.7
    thickness: int = 2


class CaptureHandler:
    """Gerencia buffers de captura (manual e contínuo) e produz overlays de estado.

    Responsabilidade: decidir quando uma janela de frames está pronta, retornar
    os frames para processamento e as linhas de overlay para a UI. Não faz
    YOLO nem I/O em disco.
    """

    def __init__(self, config: PreviewConfig) -> None:
        self._config = config
        self._capturing = False
        self._frame_buffer: list[np.ndarray] = []
        self._sliding_buffer: deque[np.ndarray] = deque(maxlen=config.effective_frames_to_capture)
        self._frames_since_process = 0
        self._windows_processed_count = 0

    def update(
        self,
        frame: np.ndarray,
        key: int,
        frame_width: int,
        frame_height: int,
    ) -> tuple[CaptureResult | None, list[OverlayLine]]:
        """Processa um novo frame e tecla, atualiza buffers e retorna resultado + overlays.

        Args:
            frame: Frame atual (cópia será armazenada se em captura).
            key: Código da tecla pressionada (cv2.waitKey).
            frame_width: Largura do frame.
            frame_height: Altura do frame.

        Returns:
            (CaptureResult se uma janela estiver pronta, lista de OverlayLine para desenhar).
        """
        result: CaptureResult | None = None
        overlays: list[OverlayLine] = []

        # Modo contínuo
        if self._config.continuous_capture:
            self._sliding_buffer.append(frame.copy())
            if len(self._sliding_buffer) == self._config.effective_frames_to_capture:
                self._frames_since_process += 1
                if self._frames_since_process >= self._config.effective_capture_interval:
                    self._frames_since_process = 0
                    self._windows_processed_count += 1
                    n = self._windows_processed_count
                    result = CaptureResult(
                        frames=list(self._sliding_buffer),
                        frame_width=frame_width,
                        frame_height=frame_height,
                        is_continuous=True,
                        continuous_window_index=n,
                    )
            overlays.extend(self._continuous_overlays(frame_height))
            return result, overlays

        # Modo manual: em captura
        if self._capturing:
            self._frame_buffer.append(frame.copy())
            n = len(self._frame_buffer)
            if n >= self._config.effective_frames_to_capture:
                result = CaptureResult(
                    frames=list(self._frame_buffer),
                    frame_width=frame_width,
                    frame_height=frame_height,
                    is_continuous=False,
                    manual_save_frames=self._config.save_frames,
                )
                self._capturing = False
                self._frame_buffer.clear()
            else:
                overlays.append(
                    OverlayLine(
                        f"Capturando {n}/{self._config.effective_frames_to_capture} (LSTM)",
                        (10, 40),
                        (0, 255, 0),
                        1.0,
                        2,
                    )
                )
            return result, overlays

        # Tecla 'c' inicia captura manual
        if key == self._config.capture_key:
            self._capturing = True
            self._frame_buffer = []
            logger.info(
                "Captura iniciada: próximos %d frames",
                self._config.effective_frames_to_capture,
            )

        return result, overlays

    def _continuous_overlays(self, frame_height: int) -> list[OverlayLine]:
        lines = [
            OverlayLine(
                f"Continuo [buffer={len(self._sliding_buffer)}/{self._config.effective_frames_to_capture}]",
                (10, 35),
                (0, 255, 255),
                0.7,
                2,
            ),
            OverlayLine(
                f"Janelas processadas: {self._windows_processed_count}",
                (10, 75),
                (0, 255, 0),
                0.7,
                2,
            ),
        ]
        if self._config.save_continuous_sequences:
            lines.append(
                OverlayLine(
                    "Salvando em data/captures/continuous/",
                    (10, 115),
                    (0, 255, 0),
                    0.6,
                    2,
                )
            )
        return lines

    def manual_output_dir(self) -> Path:
        """Diretório de saída para captura manual (timestamp)."""
        stamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        return self._config.capture_output_path / stamp
