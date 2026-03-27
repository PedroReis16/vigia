from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from src.core.config import Settings
from src.core.logging import setup_logging
from src.vision import WebcamPreviewService

# Sentinel: quando video_source não é passado, usa o valor do .env
_USE_ENV_VIDEO_SOURCE: Any = object()


class LocalRuntime:
    """Runtime local: pode rodar em modo padrão (.env) ou em modo preview (CLI --webcam / --video)."""

    def __init__(
        self,
        settings: Settings,
        *,
        video_source: Path | str | None = _USE_ENV_VIDEO_SOURCE,
    ) -> None:
        """Inicializa o runtime.

        Args:
            settings: Configuração carregada do ambiente.
            video_source: _USE_ENV_VIDEO_SOURCE = usa settings.webcam_debug_video;
                None = webcam (CLI --webcam); path = vídeo (CLI --video).
        """
        self._settings = settings
        if video_source is _USE_ENV_VIDEO_SOURCE:
            source = settings.webcam_debug_video
        else:
            source = video_source
        source_path: Path | None = None
        if source is not None:
            source_path = source if isinstance(source, Path) else Path(source)

        self._webcam_preview = WebcamPreviewService(
            camera_index=settings.webcam_indices,
            window_name=settings.webcam_window_name,
            flip_horizontal=settings.webcam_flip_horizontal,
            yolo_model_path=settings.yolo_model_path,
            video_source=source_path,  # None = webcam, Path = arquivo de vídeo
            frames_to_capture=settings.frame_interval,
        )

    def run(self) -> None:
        """Modo padrão: obedece WEBCAM_PREVIEW_ENABLED do .env."""
        setup_logging(self._settings.log_level)

        if self._settings.webcam_preview_enabled:
            self._webcam_preview.run_blocking()
            return

        print(
            "WEBCAM_PREVIEW_ENABLED está false. "
            "Defina WEBCAM_PREVIEW_ENABLED=true no .env ou use: python -m src.main --webcam"
        )

        try:
            while True:
                time.sleep(0.5)
        except KeyboardInterrupt:
            self._webcam_preview.stop()

    def run_preview(self) -> None:
        """Modo preview via CLI (--webcam ou --video): inicia a janela e bloqueia até fechar."""
        setup_logging(self._settings.log_level)
        self._webcam_preview.run_blocking()
