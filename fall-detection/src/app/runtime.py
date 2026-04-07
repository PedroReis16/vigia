"""Orquestra processos: captura (câmera/pose) e análise ML em paralelo."""

from __future__ import annotations

from multiprocessing import Process
import time

from app.capture.runner import run_capture
from app.config import Settings
from app.core.runner import run_analysis


def run(settings: Settings) -> None:
    """Inicia de forma paralela os processos de captura e análise dos movimentos e quedas."""

    # `args` precisa ser uma tupla: `(settings)` em Python é só o valor, não um 1-tuple.
    capture_process = Process(target=run_capture, args=(settings,))
    analysis_process = Process(target=run_analysis, args=(settings,))

    capture_process.start()
    analysis_process.start()

    # Verificação de status dos processos
    while True:
        if not capture_process.is_alive() or not analysis_process.is_alive():
            print("Um processo finalizou. Encerrando os demais processos...")
            capture_process.terminate()
            analysis_process.terminate()
            break
        time.sleep(0.5)

    capture_process.join()
    analysis_process.join()
    print("Processos finalizados")
