"""
Ponto de entrada do programa
"""

import logging
from multiprocessing import Event, Process, Queue
import time

from capture import run_capture
from integration import run_fiware
from integration.fall_ipc import drain_fall_queue
from shared import get_identity_path, get_network_path
from shared.log_config import configure_logging
from streaming import run_stream
from streaming.frame_shm import FrameShmRing
from streaming.mp_compat import prepare_multiprocessing, stop_child_process

logger = logging.getLogger(__name__)


def kill_task(task: Process | None) -> None:
    """
    Mata a tarefa do processo (terminate imediato).
    """
    if task is None:
        return
    if task.is_alive():
        task.terminate()
    task.join(timeout=2.0)


def _require_provisioned() -> None:
    identity = get_identity_path()
    network = get_network_path()
    missing = [str(p) for p in (identity, network) if not p.exists()]
    if missing:
        raise FileNotFoundError(
            "Dispositivo não provisionado (ficheiros em falta: "
            + ", ".join(missing)
            + "). O vigia-bootstrap deve completar o pareamento."
        )


def _start_stream_task(frame_shm_name: str, stream_event: Event) -> Process:
    task = Process(
        target=run_stream,
        args=(frame_shm_name, stream_event),
        name="stream",
    )
    task.start()
    return task


def main():
    """
    Executa a rotina principal do programa (captura + Fiware + streaming sob demanda).
    """
    configure_logging("main")
    _require_provisioned()

    stream_event = Event()
    frame_shm = FrameShmRing.create()
    fall_queue: Queue = Queue(maxsize=8)

    fiware_task = Process(
        target=run_fiware,
        args=(stream_event, fall_queue),
        name="fiware",
    )
    capture_task = Process(
        target=run_capture,
        args=(stream_event, frame_shm.name, fall_queue),
        name="capture",
    )
    stream_task: Process | None = None

    fiware_task.start()
    capture_task.start()

    try:
        while True:
            if not capture_task.is_alive():
                capture_task.terminate()

            wants_stream = stream_event.is_set()
            stream_alive = stream_task is not None and stream_task.is_alive()

            if wants_stream and not stream_alive:
                frame_shm.reset_sequence()
                stream_task = _start_stream_task(frame_shm.name, stream_event)
            elif not wants_stream and stream_alive:
                stop_child_process(stream_task)
                stream_task = None
                frame_shm.reset_sequence()

            time.sleep(0.5)
    finally:
        stream_event.clear()
        stop_child_process(stream_task)
        kill_task(fiware_task)
        kill_task(capture_task)
        frame_shm.reset_sequence()
        frame_shm.close()
        frame_shm.unlink()
        drain_fall_queue(fall_queue)


if __name__ == "__main__":
    prepare_multiprocessing()
    try:
        main()
    except KeyboardInterrupt:
        logging.getLogger(__name__).info("Interrompido pelo usuário")
