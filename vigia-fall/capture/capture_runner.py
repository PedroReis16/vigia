"""
Executa a captura de vídeo
"""

from concurrent.futures import ThreadPoolExecutor
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
from capture.capture_stream import is_streaming, shutdown_stream, stop_stream, stream_video


def _opencv_has_gui() -> bool:
    """False em builds headless (placa / PyInstaller) — imshow/waitKey não existem."""
    try:
        info = cv2.getBuildInformation()
    except Exception:
        return False
    markers = ("GTK", "Cocoa", "QT", "Win32 UI", "OpenGL")
    return any(marker in info for marker in markers)


def run_capture(stream_event: EventType | None = None):
    """
    Executa a captura de vídeo
    """

    if stream_event is not None:
        init_stream_event(stream_event)

    frame_worker = None
    executor = None
    show_video = False

    try:
        settings = get_settings()
        show_video = settings.show_video
        if show_video and not _opencv_has_gui():
            print(
                "SHOW_VIDEO=true, mas o OpenCV é headless "
                "(opencv-python-headless). Use requirements-debug.txt "
                "no venv local, ou SHOW_VIDEO=false na placa."
            )
            show_video = False

        cap = cv2.VideoCapture(settings.capture_source)

        if not cap.isOpened():
            raise ValueError(
                f"Não foi possível abrir a câmera {settings.capture_source}"
            )

        last_capture = time.monotonic()

        capture_interval = 1.0 / settings.frame_rate

        frame_worker = get_worker()

        executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="frame-worker")
        executor.submit(frame_worker.run)

        while True:
            ret, frame = cap.read()

            if not ret:
                break

            now = time.monotonic()

            if now - last_capture > capture_interval:
                frame_worker.insert_raw_frame(frame.copy(), now)
                last_capture = now

            flipped_frame = cv2.flip(frame, 1)
            if show_video:
                cv2.imshow("Preview movimentos", flipped_frame)

                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break

            # Thumbnail para a API (cadência interna ~60s; não bloqueia captura).
            maybe_upload_thumbnail(flipped_frame)

            if get_stream_status():
                stream_video(flipped_frame)
            elif is_streaming():
                stop_stream()

        cap.release()
    except Exception as e:
        print(f"Erro ao executar a captura: {e}")
        raise e
    finally:
        shutdown_stream()
        # HighGUI (waitKey/imshow/destroy*) não existe em builds headless do OpenCV.
        if show_video:
            cv2.destroyAllWindows()
        if frame_worker is not None:
            frame_worker.stop()
        if executor is not None:
            executor.shutdown(wait=True, cancel_futures=True)
