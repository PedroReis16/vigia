"""Orquestra processos: captura (câmera/pose) e análise ML em paralelo."""

from __future__ import annotations

from multiprocessing import Process

from app.capture.runner import run_capture
from app.config import Settings
from app.ml.runner import run_analysis


def run(settings: Settings) -> None:
    """Inicia de forma paralela os processos de captura e análise dos movimentos e quedas."""

    # `args` precisa ser uma tupla: `(settings)` em Python é só o valor, não um 1-tuple.
    capture_process = Process(target=run_capture, args=(settings,))
    analysis_process = Process(target=run_analysis, args=(settings,))

    capture_process.start()
    analysis_process.start()

    capture_process.join()
    analysis_process.join()

    if capture_process.exitcode != 0:
        raise RuntimeError(f"Capture process exited with code {capture_process.exitcode}")
    if analysis_process.exitcode != 0:
        raise RuntimeError(f"Analysis process exited with code {analysis_process.exitcode}")