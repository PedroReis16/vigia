import shutil
import socket
import struct
import urllib.error
import urllib.request
import cv2
import os
import queue
import threading
import time
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()
DATA_PATH = os.getenv("DATA_PATH")


def _parse_tcp_ingest_addr(raw: str) -> tuple[str, int] | None:
    """
    Destino do socket TCP do vigia-stream (4 bytes LE + JPEG), não HTTP/WebSocket.
    Aceita host:porta, URLs com path (/stream é ignorado) e ws(s):// (só host/porta).
    """
    s = raw.strip()
    if not s:
        return None
    lower = s.lower()
    for prefix in ("tcp://", "http://", "https://", "ws://", "wss://"):
        if lower.startswith(prefix):
            s = s[len(prefix) :]
            break
    if "/" in s:
        s = s.split("/", 1)[0]
    if ":" in s:
        host, _, port_s = s.rpartition(":")
        host = host.strip()
        if not host:
            return None
        try:
            port = int(port_s)
        except ValueError:
            return None
    else:
        host, port = s, 8090
    # Em docker local, ws://…:8091 é o Gin; o ingest TCP da câmera no Go é :8090
    if port == 8091:
        port = 8090
    return (host, port)


def _tcp_stream_target() -> tuple[str, int] | None:
    for key in ("STREAM_TCP_ADDR", "STREAM_WS_URL"):
        raw = (os.getenv(key) or "").strip()
        if not raw:
            continue
        t = _parse_tcp_ingest_addr(raw)
        if t:
            return t
    return None


STREAM_INGEST_URL = (os.getenv("STREAM_INGEST_URL") or "").strip()
STREAM_INGEST_TOKEN = (os.getenv("STREAM_INGEST_TOKEN") or "").strip()
STREAM_TARGET = _tcp_stream_target()
if not STREAM_INGEST_URL and STREAM_TARGET is None:
    print(
        "Aviso: defina STREAM_INGEST_URL=https://…/ingest (via Traefik) ou "
        "STREAM_TCP_ADDR=host:porta (TCP :8090).",
        flush=True,
    )
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
                        try:
                            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                        except OSError:
                            pass
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

    _stream_queue = queue.Queue(maxsize=8)
    _stream_thread = threading.Thread(
        target=worker, name="tcp-stream", daemon=True
    )
    _stream_thread.start()


def _start_http_ingest_worker(url: str, token: str) -> None:
    global _stream_queue, _stream_thread

    def worker() -> None:
        assert _stream_queue is not None
        while True:
            job = _stream_queue.get()
            if job is None:
                break
            while True:
                try:
                    req = urllib.request.Request(
                        url, data=job, method="POST"
                    )
                    req.add_header("Content-Type", "application/octet-stream")
                    if token:
                        req.add_header("X-Vigia-Ingest-Token", token)
                    with urllib.request.urlopen(req, timeout=20) as resp:
                        if resp.status not in (200, 204):
                            time.sleep(0.25)
                            continue
                    break
                except (OSError, urllib.error.HTTPError):
                    time.sleep(0.25)

    _stream_queue = queue.Queue(maxsize=2)
    _stream_thread = threading.Thread(
        target=worker, name="http-ingest", daemon=True
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


if STREAM_INGEST_URL:
    _start_http_ingest_worker(STREAM_INGEST_URL, STREAM_INGEST_TOKEN)
elif STREAM_TARGET:
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