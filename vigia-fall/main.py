"""
Ponto de entrada do programa
"""

from multiprocessing import Event, Process
import time
from capture import run_capture
from integration import run_fiware
from shared import get_identity_path, get_network_path


def kill_task(task: Process) -> None:
    """
    Mata a tarefa do processo
    """
    task.terminate()
    task.join()


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


def main():
    """
    Executa a rotina principal do programa (captura + Fiware).
    """
    _require_provisioned()

    stream_event = Event()

    fiware_task = Process(target=run_fiware, args=(stream_event,))
    capture_task = Process(target=run_capture, args=(stream_event,))

    fiware_task.start()
    capture_task.start()

    try:
        while True:
            is_all_running = capture_task.is_alive()

            if not is_all_running:
                capture_task.terminate()

            time.sleep(0.5)
    finally:
        kill_task(fiware_task)
        kill_task(capture_task)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Interrompido pelo usuário")
