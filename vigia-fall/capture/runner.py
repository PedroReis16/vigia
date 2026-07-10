from concurrent.futures import ThreadPoolExecutor
import time
import cv2

from shared import get_settings
from capture.frame_worker import FrameWorker

def run_capture_async():
    """
    Executa a captura de vídeo
    """

    try:
        settings = get_settings()

        cap = cv2.VideoCapture(settings.capture_source)

        if not cap.isOpened():
            raise ValueError(f"Não foi possível abrir a câmera {settings.capture_source}")

        show_video = settings.show_video

        key = cv2.waitKey(1) & 0xFF
        
        last_capture = time.monotonic()

        capture_interval = 1.0 / settings.frame_rate
        
        worker = FrameWorker(settings.frame_rate)

        executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="frame-worker")
        executor.submit(worker.run)

        while True:
            ret, frame = cap.read()

            if not ret:
                break

            now = time.monotonic()

            if now - last_capture > capture_interval:
                worker.insert(frame.copy())
                last_capture = now

            if show_video:
                display = cv2.flip(frame, 1)
                cv2.imshow("Visualização de movimentos", display)
                
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

            if key == ord('q'):
                break
            
        cap.release()
    except Exception as e:
        print(f"Erro ao executar a captura: {e}")
        raise e
    finally:
        cv2.destroyAllWindows()
        worker.stop()
        executor.shutdown(wait=True, cancel_futures=True)

