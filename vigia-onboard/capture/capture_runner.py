"""Processo de captura de imagens."""

from __future__ import annotations

import logging
from typing import Any

import cv2  # type: ignore

from shared.settings import get_settings
from core import save_points, start_core_worker, stop_core_worker

from .pose_extract import unpack_raw_points
from .yolo_model import get_yolo_model

logger = logging.getLogger(__name__)

_BLUR_KSIZE = 51
_YOLO_STREAM_KWARGS: dict[str, Any] = {
    "stream": True,
    "persist": True,
    "device": "cpu",
    "conf": 0.25,
    "verbose": False,
    "tracker": "botsort.yaml",
    "imgsz": 320,
    "classes": [0],
    "rect": False,
}


def _is_file_source(source: int | str) -> bool:
    return isinstance(source, str)


def _source_label(source: int | str) -> str:
    if _is_file_source(source):
        return f"vídeo {source}"
    return f"câmera {source}"


def _opencv_has_gui() -> bool:
    """False em builds headless (placa / PyInstaller) — imshow/waitKey não existem."""
    try:
        info = cv2.getBuildInformation()
    except Exception:
        return False
    markers = ("GTK", "Cocoa", "QT", "Win32 UI", "OpenGL")
    return any(marker in info for marker in markers)


def _stream_results(model: Any, source: int | str) -> Any:
    """YOLO track em modo stream: um Results por frame, IDs persistentes."""
    return model.track(source, **_YOLO_STREAM_KWARGS)


def _blur_boxes(image: Any, result: Any, ksize: int = _BLUR_KSIZE) -> Any:
    """Aplica blur nas boxes detectadas (classe pessoa) e devolve uma cópia."""
    preview = image.copy()
    boxes = getattr(result, "boxes", None)
    xyxy = getattr(boxes, "xyxy", None) if boxes is not None else None
    if xyxy is None:
        return preview

    height, width = preview.shape[:2]
    for box in xyxy:
        x1, y1, x2, y2 = (int(v) for v in box[:4])
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(width, x2), min(height, y2)
        if x2 <= x1 or y2 <= y1:
            continue
        roi = preview[y1:y2, x1:x2]
        if roi.size:
            preview[y1:y2, x1:x2] = cv2.blur(roi, (ksize, ksize))
    return preview


def _should_restart_stream(
    source: int | str,
    capture_loop: bool,
    had_frame: bool,
    interrupted: bool,
) -> bool:
    return (
        had_frame
        and not interrupted
        and _is_file_source(source)
        and capture_loop
    )


def run_capture() -> None:
    """Loop principal: lê a fonte em stream YOLO e mostra preview se pedido."""
    show_video = False
    cap = None

    try:
        settings = get_settings()
        source = settings.capture_source
        show_video = settings.show_video
        capture_loop = settings.capture_loop
        yolo_model = get_yolo_model()
        logger.info(
            "YOLO carregado: %s",
            getattr(yolo_model, "ckpt_path", settings.yolo_model),
        )

        if show_video and not _opencv_has_gui():
            logger.warning(
                "SHOW_VIDEO=true, mas o OpenCV é headless; preview desativado."
            )
            show_video = False

        cap = cv2.VideoCapture(source)

        if not cap.isOpened():
            raise ValueError(
                f"Não foi possível abrir a fonte de captura ({_source_label(source)})"
            )
        # O loader do YOLO reabre a fonte; libertar para não bloquear a câmara.
        cap.release()
        cap = None

        logger.info("Captura iniciada (%s)", _source_label(source))
        interrupted = False
        start_core_worker()

        while True:
            had_frame = False
            for result in _stream_results(yolo_model, source):
                had_frame = True
                if show_video and cv2.waitKey(1) & 0xFF == ord("q"):
                    interrupted = True
                    break

                save_points(unpack_raw_points(result))

                frame = result.orig_img

                # Frames para clipe/streaming serão via memória partilhada.
                preview = (
                    _blur_boxes(frame, result) if settings.blur_video else frame
                )
                #TODO: Os clipes serão montados até aqui, com o blur aplicado. O plot é aplicado somente para o show

                preview = result.plot(img=preview) if settings.show_plot else preview

                if show_video:
                    cv2.imshow("Preview movimentos", preview)

            if not _should_restart_stream(
                source, capture_loop, had_frame, interrupted
            ):
                break

    except Exception as exc:
        logger.error("Erro ao executar a captura: %s", exc)
        raise
    finally:
        stop_core_worker()
        if show_video:
            cv2.destroyAllWindows()
        if cap is not None:
            cap.release()
        logger.info("Captura encerrada")
