"""
Ponto de entrada do programa
"""

from multiprocessing import Process
import time
from capture import run_capture
from integration import initialize_device, run_fiware
import asyncio


def kill_task(task: Process) -> None:
    """
    Mata a tarefa do processo
    """
    task.terminate()
    task.join()


async def main():
    """
    Executa a rotina principal do programa
    """

    await initialize_device()

    fiware_task = Process(target=run_fiware)
    # capture_task = Process(target=run_capture)
    # integration_task = Process(target=run_device_integration_async)

    fiware_task.start()
    # capture_task.start()
    # integration_task.start()

    try:
        while True:

            is_all_running = fiware_task.is_alive()
            # is_all_running = capture_task.is_alive() and integration_task.is_alive()

            if not is_all_running:
                fiware_task.terminate()
            #     integration_task.terminate()
            #     capture_task.terminate()
            #     break

            time.sleep(0.5)
    finally:
        kill_task(fiware_task)
        # kill_task(capture_task)
        # kill_task(integration_task)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Interrompido pelo usuário")
