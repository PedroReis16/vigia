"""Processo de captura de imagens."""

from __future__ import annotations

import logging
from typing import Any

from .settings import get_settings
from .yolo_model import get_yolo_model

logger = logging.getLogger(__name__)


def _is_file_source(source: int | str) -> bool:
    return isinstance(source, str)


def _source_label(source: int | str) -> str:
    if _is_file_source(source):
        return f"vídeo {source}"
    return f"câmera {source}"


def _opencv() -> Any:
    import cv2

    return cv2


def _opencv_has_gui(cv2: Any) -> bool:
    """False em builds headless (placa / PyInstaller) — imshow/waitKey não existem."""
    try:
        info = cv2.getBuildInformation()
    except Exception:
        return False
    markers = ("GTK", "Cocoa", "QT", "Win32 UI", "OpenGL")
    return any(marker in info for marker in markers)


def run_capture() -> None:
    """Loop principal: lê a fonte, corre YOLO pose e mostra preview se pedido."""
    cv2 = _opencv()
    show_video = False
    cap = None

    try:
        settings = get_settings()
        source = settings.capture_source
        show_video = settings.show_video
        show_yolo_plot = settings.show_yolo_plot
        capture_loop = settings.capture_loop
        yolo_model = get_yolo_model()
        logger.info(
            "YOLO carregado: %s",
            getattr(yolo_model, "ckpt_path", settings.yolo_model),
        )

        if show_video and not _opencv_has_gui(cv2):
            logger.warning(
                "SHOW_VIDEO=true, mas o OpenCV é headless; preview desativado."
            )
            show_video = False

        cap = cv2.VideoCapture(source)
        if not cap.isOpened():
            raise ValueError(
                f"Não foi possível abrir a fonte de captura ({_source_label(source)})"
            )

        logger.info("Captura iniciada (%s)", _source_label(source))
        while True:
            if show_video and cv2.waitKey(1) & 0xFF == ord("q"):
                break

            ret, frame = cap.read()
            if not ret:
                if _is_file_source(source) and capture_loop:
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    continue
                break

            results = yolo_model.predict(frame, verbose=False)
            if show_video:
                preview = results[0].plot() if show_yolo_plot else frame
                cv2.imshow("Preview movimentos", preview)

    except Exception as exc:
        logger.error("Erro ao executar a captura: %s", exc)
        raise
    finally:
        if show_video:
            cv2.destroyAllWindows()
        if cap is not None:
            cap.release()
        logger.info("Captura encerrada")
