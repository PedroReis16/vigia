"""Loop contínuo: leitura da câmera, enfileiramento de pose/CSV, stream e preview."""

from __future__ import annotations

import time

import cv2
import zmq

from app.capture.loop.capture_loop_context import CaptureLoopContext
from app.config.frame_codec import encode_numpy_frame
from app.config.ipc import FRAMES_TOPIC, bind_frame_pub_socket
from app.logging import get_logger


logger = get_logger("capture")

def disparar_alerta() -> None:
    """Dispara o alerta de queda."""
    logger.warning("alerta de queda disparado")

def run_capture_loop(ctx: CaptureLoopContext) -> None:
    """Loop contínuo: leitura da câmera, enfileiramento de pose/CSV, stream e preview."""

    try:
        context = zmq.Context()
        socket = context.socket(zmq.PUB)
        bind_frame_pub_socket(socket)
        time.sleep(0.5)

        while True:
            ret, frame = ctx.cap.read()
            if not ret:
                break

            payload = encode_numpy_frame(frame)
            socket.send_multipart([FRAMES_TOPIC, payload])

            if ctx.show_video:
                display = cv2.flip(frame, 1)
                cv2.imshow("Detection", display)
                key = cv2.waitKey(1) & 0xFF
                if key == ord("q"):
                    break

    finally:
        ctx.cap.release()
        cv2.destroyAllWindows()
        socket.close()
        context.term()