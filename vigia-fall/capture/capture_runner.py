"""
Executa a captura de vídeo
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import logging
from multiprocessing.queues import Queue as MpQueue
from multiprocessing.synchronize import Event as EventType
import time
import cv2  # pyright: ignore[reportMissingImports]

from shared import (
    get_settings,
    get_stream_status,
    init_stream_event,
)
from shared.log_config import configure_logging
from capture.frame_worker import get_worker
from capture.frame_uploader import maybe_upload_thumbnail
from integration.fall_ipc import init_fall_queue
from streaming.frame_shm import FrameShmRing

logger = logging.getLogger(__name__)


def _opencv_has_gui() -> bool:
    """False em builds headless (placa / PyInstaller) — imshow/waitKey não existem."""
    try:
        info = cv2.getBuildInformation()
    except Exception:
        return False
    markers = ("GTK", "Cocoa", "QT", "Win32 UI", "OpenGL")
    return any(marker in info for marker in markers)


def _is_file_source(source: int | str) -> bool:
    return isinstance(source, str)


def _source_label(source: int | str) -> str:
    if _is_file_source(source):
        return f"vídeo {source}"
    return f"câmera {source}"


def _resolve_stream_fps(cap: cv2.VideoCapture) -> int:
    cap_prop_fps = getattr(cv2, "CAP_PROP_FPS", 5)
    raw = cap.get(cap_prop_fps)
    fps = int(raw) if raw and raw > 0 else 30
    if fps > 120:
        fps = 30
    return max(fps, 1)


def run_capture(
    stream_event: EventType | None = None,
    frame_shm_name: str | None = None,
    fall_queue: MpQueue | None = None,
):
    """
    Executa a captura de vídeo.

    Com streaming ativo, lê a câmera em full-rate e escreve frames flipados
    na shared memory. A classificação YOLO permanece limitada a ``frame_rate``.
    """
    configure_logging("capture")

    if stream_event is not None:
        init_stream_event(stream_event)
    if fall_queue is not None:
        init_fall_queue(fall_queue)

    frame_shm = FrameShmRing.attach(frame_shm_name) if frame_shm_name else None

    frame_worker = None
    executor = None
    show_video = False
    cap = None

    try:
        settings = get_settings()
        source = settings.capture_source
        show_video = settings.show_video
        if show_video and not _opencv_has_gui():
            logger.warning(
                "SHOW_VIDEO=true, mas o OpenCV é headless "
                "(opencv-python-headless). Use requirements-debug.txt "
                "no venv local, ou SHOW_VIDEO=false na placa."
            )
            show_video = False

        cap = cv2.VideoCapture(source)

        if not cap.isOpened():
            raise ValueError(
                f"Não foi possível abrir a fonte de captura ({_source_label(source)})"
            )

        last_classify = 0.0
        classify_interval = 1.0 / settings.frame_rate
        stream_fps = _resolve_stream_fps(cap)

        frame_worker = get_worker()

        executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="frame-worker")
        executor.submit(frame_worker.run)

        while True:
            now = time.monotonic()
            streaming = frame_shm is not None and get_stream_status()

            if not streaming and now - last_classify < classify_interval:
                if show_video and cv2.waitKey(1) & 0xFF == ord("q"):
                    break
                if not show_video:
                    time.sleep(0.001)
                continue

            ret, frame = cap.read()

            if not ret:
                if _is_file_source(source) and settings.capture_loop:
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    continue
                break

            flipped_frame = cv2.flip(frame, 1)

            if now - last_classify >= classify_interval:
                last_classify = now
                frame_worker.insert_raw_frame(frame.copy(), now)

            if show_video:
                cv2.imshow("Preview movimentos", flipped_frame)

                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break

            maybe_upload_thumbnail(flipped_frame)

            if streaming:
                frame_shm.write(flipped_frame, stream_fps)

        if cap is not None:
            cap.release()
    except Exception as e:
        logger.error("Erro ao executar a captura: %s", e)
        raise e
    finally:
        if frame_shm is not None:
            frame_shm.close()
        if show_video:
            cv2.destroyAllWindows()
        if frame_worker is not None:
            frame_worker.stop()
        if executor is not None:
            executor.shutdown(wait=True, cancel_futures=True)


def main() -> None:
    """
    Ponto de entrada standalone do módulo de captura (sem Fiware/API).

    Uso: python -m capture  (a partir de vigia-fall/)
    """
    configure_logging("capture")
    try:
        run_capture()
    except KeyboardInterrupt:
        logger.info("Interrompido pelo usuário")
