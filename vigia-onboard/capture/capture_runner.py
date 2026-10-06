"""Processo de captura de imagens."""

from __future__ import annotations

import logging
import time
from typing import Any

import cv2  # type: ignore

from shared.capture_gate import (
    capture_allowed,
    clear_capture_pid,
    consume_capture_restart,
    restart_pending,
    write_capture_pid,
)
from shared.clips_config import apply_persisted_clips
from shared.live_frame_shm import DEFAULT_MAX_PAYLOAD, LiveFrameShm
from shared.settings import get_settings
from core import save_points, start_core_worker, stop_core_worker
from stream import export_active, prepare_multiprocessing, start_supervisor, stop_supervisor

from .pose_extract import unpack_raw_points
from .yolo_model import get_yolo_model

logger = logging.getLogger(__name__)

_GATE_POLL_S = 0.2
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


def _read_fps(cap: Any) -> float | None:
    try:
        raw = float(cap.get(cv2.CAP_PROP_FPS))
    except (TypeError, ValueError):
        return None
    if raw != raw or raw < 1:
        return None
    return raw


def _source_fps(cap: Any, fallback: int) -> int:
    """FPS da fonte para o stream. Sem valor válido, usa ``FRAME_RATE``."""
    raw = _read_fps(cap)
    if raw is None:
        try:
            cap.read()
        except Exception:
            return fallback
        raw = _read_fps(cap)
    if raw is None:
        return fallback
    return max(1, int(round(raw)))


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


def _open_live_shm(settings) -> LiveFrameShm | None:
    try:
        return LiveFrameShm.open_or_create(
            settings.live_shm_name,
            max_payload=max(DEFAULT_MAX_PAYLOAD, settings.clip_max_payload),
        )
    except Exception as error:
        logger.warning("Live SHM indisponível: %s", error)
        return None


def _wait_until_allowed() -> None:
    """Bloqueia até identity.json, network.json e ausência de capture.hold."""
    announced = False
    while not capture_allowed():
        if not announced:
            logger.info(
                "Captura bloqueada até o provisionamento (identity, network, sem hold)"
            )
            announced = True
        time.sleep(_GATE_POLL_S)


def _run_capture_session() -> str:
    """Uma sessão de câmera. Devolve done, hold ou restart."""
    if restart_pending():
        consume_capture_restart()

    show_video = False
    cap = None
    live_shm: LiveFrameShm | None = None
    write_capture_pid()

    try:
        prepare_multiprocessing()
        settings = get_settings()
        source = settings.capture_source
        show_video = settings.show_video
        capture_loop = settings.capture_loop
        fallback_fps = max(1, int(settings.frame_rate))
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

        live_shm = _open_live_shm(settings)

        cap = cv2.VideoCapture(source)

        if not cap.isOpened():
            raise ValueError(
                f"Não foi possível abrir a fonte de captura ({_source_label(source)})"
            )
        source_fps = _source_fps(cap, fallback_fps)
        # O loader do YOLO reabre a fonte; libertar para não bloquear a câmara.
        cap.release()
        cap = None

        logger.info(
            "Captura iniciada (%s, stream %s fps)",
            _source_label(source),
            source_fps,
        )
        interrupted = False
        start_core_worker()
        if live_shm is not None:
            apply_persisted_clips()
            start_supervisor(
                live_shm.name,
                clip_shm_name=settings.clip_shm_name,
                live_shm=live_shm,
            )

        while True:
            had_frame = False
            for result in _stream_results(yolo_model, source):
                if not capture_allowed():
                    return "hold"
                if restart_pending():
                    return "restart"
                had_frame = True
                if show_video and cv2.waitKey(1) & 0xFF == ord("q"):
                    interrupted = True
                    break

                save_points(unpack_raw_points(result))

                frame = result.orig_img
                preview = (
                    _blur_boxes(frame, result) if settings.blur_video else frame
                )

                if live_shm is not None and export_active():
                    live_shm.write(preview, source_fps)

                preview = result.plot(img=preview) if settings.show_plot else preview

                if show_video:
                    cv2.imshow("Preview movimentos", preview)

            if not capture_allowed():
                return "hold"
            if restart_pending():
                return "restart"
            if not _should_restart_stream(
                source, capture_loop, had_frame, interrupted
            ):
                return "done"

    except Exception as exc:
        logger.error("Erro ao executar a captura: %s", exc)
        raise
    finally:
        clear_capture_pid()
        stop_supervisor()
        stop_core_worker()
        if live_shm is not None:
            live_shm.reset_sequence()
            live_shm.close()
            live_shm.unlink()
        if show_video:
            cv2.destroyAllWindows()
        if cap is not None:
            cap.release()
        logger.info("Captura encerrada")


def run_capture() -> None:
    """Espera o gate e corre sessões até a fonte terminar sem restart nem hold."""
    while True:
        _wait_until_allowed()
        reason = _run_capture_session()
        if reason == "done":
            return
