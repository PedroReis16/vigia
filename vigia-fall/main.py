"""
Ponto de entrada do programa
"""

from multiprocessing import Process
import time
from capture import run_capture
from integration import initialize_device_async, run_device_integration_async
from connection import init_register_beacon
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

    await init_register_beacon()

    initialize_device_async()

    # capture_task = Process(target=run_capture)
    # integration_task = Process(target=run_device_integration_async)
    # bluetooth_task = Process(target=init_register_beacon)

    # capture_task.start()
    # integration_task.start()
    # bluetooth_task.start()
    
    try:
        while True:

            # is_all_running = bluetooth_task.is_alive()
            # is_all_running = capture_task.is_alive() and integration_task.is_alive()

            # if not is_all_running:
            #     integration_task.terminate()
            #     capture_task.terminate()
            #     break

            # if not is_all_running:
            #     bluetooth_task.terminate()
                # break

            time.sleep(0.5)
    finally:
        # kill_task(capture_task)
        # kill_task(integration_task)
        # kill_task(bluetooth_task)
        pass
        
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Interrompido pelo usuário")