import time

from src.core.config import Settings
from src.core.logging import setup_logging
from src.vision import WebcamPreviewService


class LocalRuntime:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._webcam_preview = WebcamPreviewService(
            camera_index=settings.webcam_index,
            window_name=settings.webcam_window_name,
            flip_horizontal=settings.webcam_flip_horizontal,
        )

    def run(self) -> None:
        setup_logging(self._settings.log_level)

        if self._settings.webcam_preview_enabled:
            self._webcam_preview.run_blocking()
            return

        print(
            "WEBCAM_PREVIEW_ENABLED está false. "
            "Defina WEBCAM_PREVIEW_ENABLED=true no .env para abrir a janela da câmera."
        )

        try:
            while True:
                time.sleep(0.5)
        except KeyboardInterrupt:
            self._webcam_preview.stop()
