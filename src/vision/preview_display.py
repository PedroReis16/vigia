"""Exibição do preview: janela OpenCV e desenho de overlays."""

from __future__ import annotations

import logging
from typing import Sequence

import cv2
import numpy as np

from src.vision.capture_handler import OverlayLine

logger = logging.getLogger(__name__)


class PreviewDisplay:
    """Janela de preview com suporte a overlays de texto.

    Responsabilidade: criar/destruir janela, desenhar frame e linhas de overlay,
    ler tecla e verificar se a janela foi fechada. Isola todo o uso do OpenCV
    para exibição.
    """

    def __init__(self, window_name: str, is_debug_video: bool = False) -> None:
        """Inicializa o display (janela é criada ao abrir).

        Args:
            window_name: Nome da janela (inclui [DEBUG VIDEO] se is_debug_video).
            is_debug_video: Se True, desenha indicador "Modo DEBUG: video".
        """
        self._window_name = f"{window_name} [DEBUG VIDEO]" if is_debug_video else window_name
        self._is_debug_video = is_debug_video
        self._opened = False

    def open(self) -> None:
        """Cria a janela redimensionável."""
        if self._opened:
            return
        cv2.namedWindow(self._window_name, cv2.WINDOW_NORMAL)
        self._opened = True
        logger.debug("Janela de preview criada: %s", self._window_name)

    def show(
        self,
        frame: np.ndarray,
        overlays: Sequence[OverlayLine] = (),
        *,
        save_message: str | None = None,
        save_message_frames_left: int = 0,
    ) -> None:
        """Exibe o frame com overlays e opcionalmente mensagem de save.

        Args:
            frame: Imagem BGR.
            overlays: Linhas de texto a desenhar (posição, cor, etc.).
            save_message: Mensagem de feedback pós-save (ex.: "Salvo em ...").
            save_message_frames_left: Frames restantes para mostrar a mensagem (0 = não mostrar).
        """
        display = frame.copy()
        h_frame = frame.shape[0]

        for line in overlays:
            cv2.putText(
                display,
                line.text,
                line.position,
                cv2.FONT_HERSHEY_SIMPLEX,
                line.font_scale,
                line.color,
                line.thickness,
            )

        if self._is_debug_video:
            cv2.putText(
                display,
                "Modo DEBUG: video",
                (10, h_frame - 20),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 255),
                2,
            )

        if save_message_frames_left > 0 and save_message:
            cv2.putText(
                display,
                save_message,
                (10, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2,
            )
            cv2.putText(
                display,
                "Sequencia salva para LSTM" if "Salvo" in save_message else "Salvando em background...",
                (10, 80),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2,
            )

        cv2.imshow(self._window_name, display)

    def wait_key(self, delay_ms: int = 1) -> int:
        """Retorna o código da tecla pressionada (ou -1 se nenhuma)."""
        return cv2.waitKey(delay_ms) & 0xFF

    def is_visible(self) -> bool:
        """Retorna False se o usuário fechou a janela (botão X)."""
        if not self._opened:
            return True
        try:
            return cv2.getWindowProperty(self._window_name, cv2.WND_PROP_VISIBLE) >= 1
        except cv2.error:
            return False

    def destroy(self) -> None:
        """Fecha a janela e libera recursos OpenCV de janelas."""
        cv2.destroyAllWindows()
        self._opened = False
        logger.debug("Janela de preview destruída")
