"""
Compatibilidade multiprocessing (fork no Linux, spawn no Windows/macOS).
"""

from __future__ import annotations

import multiprocessing
from multiprocessing import Process
from multiprocessing.queues import Queue as MpQueue

from streaming.frame_ipc import drain_queue


def prepare_multiprocessing() -> None:
    """
    Preparação segura para entrypoints.

    ``freeze_support`` é necessário no Windows (e bundles PyInstaller) quando
    o programa usa ``Process``. Idempotente nas demais plataformas.
    """
    multiprocessing.freeze_support()


def stop_child_process(
    task: Process | None,
    *,
    frame_queue: MpQueue | None = None,
    join_timeout: float = 5.0,
) -> None:
    """
    Encerra um processo filho preferindo join limpo (Event já limpo) e só
    então ``terminate``. Evita corromper a Queue IPC no start method ``spawn``
    (Windows/macOS) ao matar o consumidor a meio de um ``get``.
    """
    if task is None:
        return

    if task.is_alive():
        task.join(timeout=join_timeout)

    if task.is_alive():
        task.terminate()
        task.join(timeout=2.0)

    if frame_queue is not None:
        drain_queue(frame_queue)
