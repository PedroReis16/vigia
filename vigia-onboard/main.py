"""Serviço Vigia: captura, integração e interface no mesmo processo pai.

O binário instalado na placa (`vigia`) arranca os três papéis e reinicia
cada um se terminar. Em desenvolvimento, `make run` continua a ser o atalho
paralelo; `python main.py` (com o venv já activo) faz o mesmo papel do serviço.
"""

from __future__ import annotations

import logging
import signal
import time
from collections.abc import Callable
from multiprocessing import Process

from stream.mp_compat import prepare_multiprocessing, stop_child_process

logger = logging.getLogger(__name__)

_POLL_S = 0.5
_RESTART_BACKOFF_S = 2.0


def _configure_logging() -> None:
    if logging.getLogger().handlers:
        return
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s %(name)s: %(message)s",
    )


def _reset_child_signals() -> None:
    """O filho herda o handler do pai no fork. Volta ao default para o systemd poder pará-lo."""
    signal.signal(signal.SIGTERM, signal.SIG_DFL)
    signal.signal(signal.SIGINT, signal.SIG_DFL)


def run_capture_child() -> None:
    """Processo de captura (YOLO + thread de classificação + workers de stream)."""
    _reset_child_signals()
    _configure_logging()
    from capture.capture_runner import run_capture

    logger.info("Captura iniciada")
    run_capture()


def run_integration_child() -> None:
    """Processo de integração FIWARE/MQTT."""
    _reset_child_signals()
    _configure_logging()
    from integration.integration_runner import run_integration

    logger.info("Integração iniciada")
    run_integration()


def run_interface_child() -> None:
    """Processo do control plane (BLE, Wi-Fi, LCD, gate, OTA)."""
    _reset_child_signals()
    _configure_logging()
    from interface.interface_runner import run_interface

    logger.info("Interface iniciada")
    run_interface()


CHILD_SPECS: tuple[tuple[str, Callable[[], None]], ...] = (
    ("capture", run_capture_child),
    ("integration", run_integration_child),
    ("interface", run_interface_child),
)


def ensure_children(
    tasks: dict[str, Process],
    *,
    now: float | None = None,
    next_start: dict[str, float] | None = None,
    process_factory: Callable[..., Process] = Process,
    backoff_s: float = _RESTART_BACKOFF_S,
    join_timeout: float = 0.2,
) -> None:
    """Garante um processo vivo por papel. Um papel que acabou espera `backoff_s`."""
    moment = time.monotonic() if now is None else now
    pending = next_start if next_start is not None else {}
    for name, target in CHILD_SPECS:
        current = tasks.get(name)
        if current is not None and current.is_alive():
            continue
        if current is not None:
            current.join(timeout=join_timeout)
            tasks.pop(name, None)
            pending.setdefault(name, moment + backoff_s)
        ready_at = pending.get(name, 0.0)
        if moment < ready_at:
            continue
        child = process_factory(target=target, name=f"vigia-{name}")
        child.start()
        tasks[name] = child
        pending.pop(name, None)
        logger.info("Processo %s iniciado (pid=%s)", name, getattr(child, "pid", None))


def stop_children(tasks: dict[str, Process]) -> None:
    """Encerra interface, integração e captura, por esta ordem."""
    for name in ("interface", "integration", "capture"):
        stop_child_process(tasks.get(name))
    tasks.clear()


def run_service() -> None:
    """Loop do serviço Vigia até SIGINT/SIGTERM."""
    _configure_logging()
    logger.info("Serviço Vigia a iniciar")
    tasks: dict[str, Process] = {}
    next_start: dict[str, float] = {}
    stop = False

    def _request_stop(signum: int, _frame: object) -> None:
        nonlocal stop
        logger.info("Sinal %s — a encerrar o serviço Vigia", signum)
        stop = True

    signal.signal(signal.SIGTERM, _request_stop)
    signal.signal(signal.SIGINT, _request_stop)

    try:
        while not stop:
            ensure_children(tasks, next_start=next_start)
            time.sleep(_POLL_S)
    finally:
        stop_children(tasks)
        logger.info("Serviço Vigia encerrado")


if __name__ == "__main__":
    prepare_multiprocessing()
    run_service()
