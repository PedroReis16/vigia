"""
Ponto de entrada do programa
"""

from multiprocessing import Event, Process, Queue
import time
from capture import run_capture
from integration import run_fiware
from shared import get_identity_path, get_network_path
from streaming import run_stream
from streaming.frame_ipc import drain_queue
from streaming.mp_compat import prepare_multiprocessing, stop_child_process


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


def _start_stream_task(frame_queue: Queue, stream_event: Event) -> Process:
    task = Process(target=run_stream, args=(frame_queue, stream_event))
    task.start()
    return task


def main():
    """
    Executa a rotina principal do programa (captura + Fiware + streaming sob demanda).
    """
    _require_provisioned()

    stream_event = Event()
    frame_queue: Queue = Queue(maxsize=2)

    fiware_task = Process(target=run_fiware, args=(stream_event,))
    capture_task = Process(target=run_capture, args=(stream_event, frame_queue))
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
                # Evita lixo de uma sessão anterior (spawn/Windows).
                drain_queue(frame_queue)
                stream_task = _start_stream_task(frame_queue, stream_event)
            elif not wants_stream and stream_alive:
                # Event já limpo pelo FIWARE → run_stream sai sozinho; join antes de terminate.
                stop_child_process(stream_task, frame_queue=frame_queue)
                stream_task = None

            time.sleep(0.5)
    finally:
        stream_event.clear()
        stop_child_process(stream_task, frame_queue=frame_queue)
        kill_task(fiware_task)
        kill_task(capture_task)
        drain_queue(frame_queue)


if __name__ == "__main__":
    prepare_multiprocessing()
    try:
        main()
    except KeyboardInterrupt:
        print("Interrompido pelo usuário")
