"""Orquestra processos: captura (câmera/pose) e análise ML em paralelo."""

from __future__ import annotations

import asyncio
import json
from multiprocessing import Event, Process
import os
from pathlib import Path
import time

from app.capture.runner import run_capture
from app.config.data_workspace import resolve_data_root
from app.config import Settings
from app.core.runner import run_analysis
from app.fiware.device_sync import load_or_create_local_device_settings
from app.integration.runner import run_integration
from app.logging import get_logger

logger = get_logger("runtime")


def _write_module_status(status_file: Path, payload: dict[str, str]) -> None:
    status_file.parent.mkdir(parents=True, exist_ok=True)
    status_file.write_text(json.dumps(payload), encoding="utf-8")


def _run_integration_process(settings: Settings, startup_ready: Event) -> None:
    # A integração prepara a configuração local (cria device.json se necessário)
    # antes de liberar os demais módulos.
    load_or_create_local_device_settings()
    startup_ready.set()
    asyncio.run(run_integration(settings))


def run(settings: Settings) -> None:
    """Inicia de forma paralela os processos de captura e análise dos movimentos e quedas."""
    data_root = resolve_data_root(settings.data_path)
    status_file = data_root / "module_status.json"
    posture_file = data_root / "posture_status.json"
    os.environ["MODULE_STATUS_FILE"] = str(status_file.resolve())
    os.environ["POSTURE_STATUS_FILE"] = str(posture_file.resolve())
    _write_module_status(
        status_file,
        {"capture": "waiting", "core": "waiting", "integration": "starting"},
    )
    _write_module_status(
        posture_file,
        {"posture_state": "unknown", "posture_changed_at": ""},
    )

    integration_startup_ready = Event()
    integration_process = Process(
        target=_run_integration_process,
        args=(settings, integration_startup_ready),
    )
    integration_process.start()

    integration_ready = integration_startup_ready.wait(timeout=10)
    if not integration_ready:
        integration_process.terminate()
        integration_process.join()
        raise RuntimeError(
            "falha ao inicializar o modulo de integracao no tempo esperado. "
            "verifique a configuracao local do dispositivo."
        )
    logger.info("integracao inicializada; iniciando captura e core.")

    # `args` precisa ser uma tupla: `(settings)` em Python é só o valor, não um 1-tuple.
    capture_process = Process(target=run_capture, args=(settings,))
    analysis_process = Process(target=run_analysis, args=(settings,))

    capture_process.start()
    analysis_process.start()

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
            logger.warning("um processo finalizou. encerrando os demais processos...")
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
    logger.info("processos finalizados")
