"""
IPC leve de fall_state (string) entre captura e processo FIWARE.
"""

from __future__ import annotations

from multiprocessing.queues import Queue as MpQueue
from queue import Empty, Full

_fall_queue: MpQueue | None = None


def init_fall_queue(queue: MpQueue) -> None:
    """
    Associa a fila compartilhada ao módulo.
    Deve ser chamado no início de cada processo filho que usa a fila.
    """
    global _fall_queue
    _fall_queue = queue


def enqueue_fall_state(label: str) -> None:
    """
    Enfileira um label de fall_state. Se a fila estiver cheia, descarta o mais antigo.
    No-op se a fila não foi inicializada (ex.: captura standalone).
    """
    if _fall_queue is None:
        return

    try:
        _fall_queue.put_nowait(label)
    except Full:
        try:
            _fall_queue.get_nowait()
        except Empty:
            pass
        try:
            _fall_queue.put_nowait(label)
        except Full:
            pass


def drain_fall_queue(queue: MpQueue | None = None) -> None:
    """Esvazia a fila de fall_state (ex.: shutdown do supervisor)."""
    target = queue if queue is not None else _fall_queue
    if target is None:
        return
    while True:
        try:
            target.get_nowait()
        except Empty:
            break
