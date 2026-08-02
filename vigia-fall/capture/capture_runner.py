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
from capture.capture_stream import is_streaming, shutdown_stream, stop_stream, stream_video


def run_capture(stream_event: EventType | None = None):
    """
    Executa a captura de vídeo
    """

    if stream_event is not None:
        init_stream_event(stream_event)

    frame_worker = None
    executor = None

    try:
        settings = get_settings()

        cap = cv2.VideoCapture(settings.capture_source)

        if not cap.isOpened():
            raise ValueError(
                f"Não foi possível abrir a câmera {settings.capture_source}"
            )

        show_video = settings.show_video

        key = cv2.waitKey(1) & 0xFF

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

            # if now - last_capture > capture_interval:
            #     frame_worker.insert_raw_frame(frame.copy())
            #     last_capture = now

            if show_video:
                display = cv2.flip(frame, 1)
                cv2.imshow("Preview", display)

                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break

            if get_stream_status():
                stream_video(frame)
            elif is_streaming():
                stop_stream()

            if key == ord("q"):
                break

        cap.release()
    except Exception as e:
        print(f"Erro ao executar a captura: {e}")
        raise e
    finally:
        shutdown_stream()
        cv2.destroyAllWindows()
        if frame_worker is not None:
            frame_worker.stop()
        if executor is not None:
            executor.shutdown(wait=True, cancel_futures=True)
