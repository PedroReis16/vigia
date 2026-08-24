"""
Executa a captura de vídeo
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from multiprocessing.queues import Queue as MpQueue
from multiprocessing.synchronize import Event as EventType
import time
import cv2  # pyright: ignore[reportMissingImports]

from shared import (
    get_settings,
    get_stream_status,
    init_stream_event,
)
from capture.frame_worker import get_worker
from capture.frame_uploader import maybe_upload_thumbnail
from streaming.frame_ipc import put_frame

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

def run_capture(
    stream_event: EventType | None = None,
    frame_queue: MpQueue | None = None,
):
    """
    Executa a captura de vídeo.

    Quando ``frame_queue`` é fornecida e o streaming está ativo, enfileira
    frames flipados para o processo de streaming via IPC.
    """

    if stream_event is not None:
        init_stream_event(stream_event)

    frame_worker = None
    executor = None
    show_video = False
    cap = None

    try:
        settings = get_settings()
        source = settings.capture_source
        show_video = settings.show_video
        if show_video and not _opencv_has_gui():
            print(
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

        last_capture = 0.0
        capture_interval = 1.0 / settings.frame_rate

        frame_worker = get_worker()

        executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="frame-worker")
        executor.submit(frame_worker.run)

        while True:
            now = time.monotonic()
            if now - last_capture < capture_interval:
                if show_video and cv2.waitKey(1) & 0xFF == ord("q"):
                    break
                continue

            ret, frame = cap.read()

            if not ret:
                if _is_file_source(source) and settings.capture_loop:
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    continue
                break

            last_capture = now
            frame_worker.insert_raw_frame(frame.copy(), now)

            flipped_frame = cv2.flip(frame, 1)
            if show_video:
                cv2.imshow("Preview movimentos", flipped_frame)

                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break

            # Thumbnail para a API (cadência interna ~60s; não bloqueia captura).
            maybe_upload_thumbnail(flipped_frame)

            if frame_queue is not None and get_stream_status():
                put_frame(frame_queue, flipped_frame)

        if cap is not None:
            cap.release()
    except Exception as e:
        print(f"Erro ao executar a captura: {e}")
        raise e
    finally:
        # HighGUI (waitKey/imshow/destroy*) não existe em builds headless do OpenCV.
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
    try:
        run_capture()
    except KeyboardInterrupt:
        print("Interrompido pelo usuário")
