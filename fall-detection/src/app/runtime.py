"""Orquestra processos: captura (câmera/pose) e análise ML em paralelo."""

from __future__ import annotations

import asyncio
import json
from multiprocessing import Process
import os
from pathlib import Path
import time

from app.capture.runner import run_capture
from app.config import Settings
from app.core.runner import run_analysis
from app.integration.runner import run_integration


def _write_module_status(status_file: Path, payload: dict[str, str]) -> None:
    status_file.parent.mkdir(parents=True, exist_ok=True)
    status_file.write_text(json.dumps(payload), encoding="utf-8")


def _run_integration_process(settings: Settings) -> None:
    asyncio.run(run_integration(settings))


def run(settings: Settings) -> None:
    """Inicia de forma paralela os processos de captura e análise dos movimentos e quedas."""
    status_file = Path(settings.data_path or ".") / "module_status.json"
    os.environ["MODULE_STATUS_FILE"] = str(status_file.resolve())
    _write_module_status(
        status_file,
        {"capture": "starting", "core": "starting", "integration": "starting"},
    )

    # `args` precisa ser uma tupla: `(settings)` em Python é só o valor, não um 1-tuple.
    capture_process = Process(target=run_capture, args=(settings,))
    analysis_process = Process(target=run_analysis, args=(settings,))
    integration_process = Process(target=_run_integration_process, args=(settings,))

    capture_process.start()
    analysis_process.start()
    integration_process.start()

    # Verificação de status dos processos
    while True:
        capture_status = "running" if capture_process.is_alive() else "stopped"
        core_status = "running" if analysis_process.is_alive() else "stopped"
        integration_status = "running" if integration_process.is_alive() else "stopped"
        _write_module_status(
            status_file,
            {
                "capture": capture_status,
                "core": core_status,
                "integration": integration_status,
            },
        )

        if not capture_process.is_alive() or not analysis_process.is_alive() or not integration_process.is_alive():
            print("Um processo finalizou. Encerrando os demais processos...")
            capture_process.terminate()
            analysis_process.terminate()
            integration_process.terminate()
            break
        time.sleep(0.5)

    capture_process.join()
    analysis_process.join()
    integration_process.join()
    _write_module_status(
        status_file,
        {"capture": "stopped", "core": "stopped", "integration": "stopped"},
    )
    print("Processos finalizados")
