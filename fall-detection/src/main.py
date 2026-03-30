import cv2
import os
import queue
import threading
import time

from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()
DATA_PATH = os.getenv("DATA_PATH")
if DATA_PATH:
    FRAMES_DIR = os.path.join(DATA_PATH.rstrip("/"), "frames")
    os.makedirs(FRAMES_DIR, exist_ok=True)
else:
    FRAMES_DIR = None

# Captura automática: quantos arquivos por segundo (0 = só manual com tecla 'p')
CAPTURES_PER_SECOND = int(os.getenv("CAPTURES_PER_SECOND", "0"))
_capture_interval = (1.0 / CAPTURES_PER_SECOND) if CAPTURES_PER_SECOND > 0 else None
_last_auto_capture = time.monotonic()
_t_session_start = time.monotonic()
_second_bucket = -1
_frame_in_second = 0

# Gravação em thread separada: o loop principal só enfileira; imwrite não bloqueia read/show.
# maxsize limita memória se o disco for mais lento que a captura (backpressure).
_save_queue: queue.Queue[tuple[str, object] | None] | None = None
_save_thread: threading.Thread | None = None


def _start_save_worker() -> None:
    global _save_queue, _save_thread

    def worker() -> None:
        assert _save_queue is not None
        while True:
            job = _save_queue.get()
            if job is None:
                break
            path, img = job
            cv2.imwrite(path, img)

    _save_queue = queue.Queue(maxsize=8)
    _save_thread = threading.Thread(target=worker, name="frame-saver", daemon=True)
    _save_thread.start()


def _stop_save_worker() -> None:
    global _save_queue, _save_thread
    if _save_queue is not None:
        _save_queue.put(None)
    if _save_thread is not None:
        _save_thread.join(timeout=5.0)
        _save_thread = None
        _save_queue = None


if FRAMES_DIR:
    _start_save_worker()

# 1. Inicializar a webcam (0 é geralmente a câmera padrão)
cap = cv2.VideoCapture(0)

item = 0


def frame_dir_for_elapsed_seconds(fr_dir: str, elapsed_sec: int) -> str:
    """Uma pasta por segundo decorrido desde o início (000000, 000001, ...)."""
    d = os.path.join(fr_dir, f"{elapsed_sec:06d}")
    os.makedirs(d, exist_ok=True)
    return d

def capture_frame(roi, now: float) -> None:
    global _last_auto_capture, _second_bucket, _frame_in_second, item

    _last_auto_capture = now
    elapsed_sec = int(now - _t_session_start)

    if elapsed_sec != _second_bucket:
        _second_bucket = elapsed_sec
        _frame_in_second = 0
    _frame_in_second += 1
    item += 1
    out_dir = frame_dir_for_elapsed_seconds(FRAMES_DIR, elapsed_sec)
    path = os.path.join(out_dir, f"frame_{_frame_in_second:04d}.png")
    # Cópia: o array do ROI é reutilizado no próximo frame; a fila grava em outra thread.
    if _save_queue is not None:
        try:
            _save_queue.put_nowait((path, roi.copy()))
        except queue.Full:
            item -= 1
            _frame_in_second -= 1
    else:
        ok = cv2.imwrite(path, roi)
        if not ok:
            item -= 1
            _frame_in_second -= 1

while True:
    # 2. Ler o frame (retorna booleano e a imagem)
    ret, frame = cap.read()

    if not ret:
        break

    height, width = frame.shape[:2]

    x1 = int(width * 0.05)  # 5% do frame para cada lado (esquerda)
    x2 = int(width * 0.95)  # 5% do frame para cada lado (direita)
    y1 = int(height * 0.05)  # 5% do frame para cada lado (topo)
    y2 = int(height * 0.95)  # 5% do frame para cada lado (base)

    roi = frame[y1:y2, x1:x2]

    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

    # Captura automática por intervalo (ex.: 10/s → a cada 0,1 s)
    if FRAMES_DIR and _capture_interval is not None:
        now = time.monotonic()
        if now - _last_auto_capture >= _capture_interval:
            capture_frame(roi, now)

    # 3. Exibir o frame
    cv2.imshow("Webcam", frame)

    key = cv2.waitKey(1) & 0xFF

    # 4. Parar ao pressionar 'q'
    if key == ord("q"):
        break

# 5. Liberar recursos
_stop_save_worker()
cap.release()
cv2.destroyAllWindows()
