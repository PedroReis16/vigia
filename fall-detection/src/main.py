import shutil
import socket
import struct
import cv2
import os
import queue
import threading
import time
from urllib.parse import urlparse

from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()
DATA_PATH = os.getenv("DATA_PATH")


def _tcp_stream_target() -> tuple[str, int] | None:
    """Host/porta do TCP de ingestão no Go (porta 8090), não WebSocket."""
    raw = (os.getenv("STREAM_TCP_ADDR") or "").strip()
    if raw:
        if ":" in raw:
            h, _, p = raw.rpartition(":")
            return (h.strip(), int(p))
        return (raw, 8090)
    ws = (os.getenv("STREAM_WS_URL") or "").strip()
    if ws.startswith("ws://"):
        u = urlparse(ws.replace("ws://", "http://", 1))
        if u.hostname:
            port = u.port or 8090
            # WS do Angular costuma ser :8091; o TCP da câmera no Go é :8090
            if port == 8091:
                return (u.hostname, 8090)
            return (u.hostname, port)
    return None


STREAM_TARGET = _tcp_stream_target()
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

_stream_queue: queue.Queue[bytes | None] | None = None
_stream_thread: threading.Thread | None = None


def _start_stream_worker(host: str, port: int) -> None:
    global _stream_queue, _stream_thread

    def worker() -> None:
        assert _stream_queue is not None
        sock: socket.socket | None = None
        while True:
            job = _stream_queue.get()
            if job is None:
                break
            payload = job
            while True:
                try:
                    if sock is None:
                        sock = socket.create_connection((host, port), timeout=2.0)
                    header = struct.pack("<I", len(payload))
                    sock.sendall(header + payload)
                    break
                except OSError:
                    if sock is not None:
                        try:
                            sock.close()
                        except OSError:
                            pass
                        sock = None
                    time.sleep(0.25)

        if sock is not None:
            try:
                sock.close()
            except OSError:
                pass

    _stream_queue = queue.Queue(maxsize=2)
    _stream_thread = threading.Thread(
        target=worker, name="tcp-stream", daemon=True
    )
    _stream_thread.start()


def _stop_stream_worker() -> None:
    global _stream_queue, _stream_thread
    if _stream_queue is not None:
        _stream_queue.put(None)
    if _stream_thread is not None:
        _stream_thread.join(timeout=5.0)
        _stream_thread = None
        _stream_queue = None


if STREAM_TARGET:
    _start_stream_worker(STREAM_TARGET[0], STREAM_TARGET[1])


def _video_capture_source() -> int | str:
    """
    Fonte para cv2.VideoCapture:
    - número (ex.: 0, 1): índice do dispositivo — no Mac, Continuity Camera / webcam virtual
      costuma ser 1 ou 2 se 0 for a webcam do notebook;
    - URL: http://... ou rtsp://... (ex.: app no iPhone que expõe MJPEG/RTSP).
    """
    raw = (os.getenv("VIDEO_CAPTURE_SOURCE") or "0").strip()
    if not raw:
        return 0
    if raw.isdigit():
        return int(raw)
    return raw


# 1. Inicializar captura (índice, URL ou caminho — ver VIDEO_CAPTURE_SOURCE no .env)
cap = cv2.VideoCapture(_video_capture_source())

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

def send_frame(frame) -> None:
    if _stream_queue is None:
        return
    ok, buf = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
    if not ok:
        return
    payload = buf.tobytes()
    try:
        _stream_queue.put_nowait(payload)
    except queue.Full:
        try:
            _stream_queue.get_nowait()
        except queue.Empty:
            pass
        try:
            _stream_queue.put_nowait(payload)
        except queue.Full:
            pass

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

    send_frame(frame)

    # 4. Parar ao pressionar 'q'
    if key == ord("q"):
        break

# 5. Liberar recursos
_stop_stream_worker()
_stop_save_worker()
cap.release()
cv2.destroyAllWindows()

if DATA_PATH:
    shutil.rmtree(DATA_PATH)