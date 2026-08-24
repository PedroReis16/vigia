"""Testes do IPC leve de fall_state."""

from __future__ import annotations

import time
from multiprocessing import Queue
from queue import Empty

import pytest

from integration import fall_ipc


def setup_function() -> None:
    fall_ipc._fall_queue = None  # noqa: SLF001


def teardown_function() -> None:
    fall_ipc._fall_queue = None  # noqa: SLF001


def _get(queue: Queue, timeout: float = 1.0):
    return queue.get(timeout=timeout)


def test_enqueue_fall_state_SemInit_NoOp() -> None:
    fall_ipc.enqueue_fall_state("fall")


def test_enqueue_fall_state_ComFila_Insere() -> None:
    queue: Queue = Queue(maxsize=8)
    fall_ipc.init_fall_queue(queue)

    fall_ipc.enqueue_fall_state("normal")
    fall_ipc.enqueue_fall_state("fall")

    assert _get(queue) == "normal"
    assert _get(queue) == "fall"


def test_enqueue_fall_state_FilaCheia_DescartaMaisAntigo() -> None:
    queue: Queue = Queue(maxsize=2)
    fall_ipc.init_fall_queue(queue)
    fall_ipc.enqueue_fall_state("a")
    fall_ipc.enqueue_fall_state("b")
    fall_ipc.enqueue_fall_state("c")

    assert _get(queue) == "b"
    assert _get(queue) == "c"
    with pytest.raises(Empty):
        queue.get(timeout=0.05)


def test_drain_fall_queue_Esvazia() -> None:
    queue: Queue = Queue(maxsize=8)
    fall_ipc.init_fall_queue(queue)
    fall_ipc.enqueue_fall_state("x")
    fall_ipc.enqueue_fall_state("y")
    time.sleep(0.05)

    fall_ipc.drain_fall_queue()

    with pytest.raises(Empty):
        queue.get(timeout=0.05)


def test_drain_fall_queue_ComArg_Esvazia() -> None:
    queue: Queue = Queue(maxsize=8)
    queue.put_nowait("z")
    time.sleep(0.05)

    fall_ipc.drain_fall_queue(queue)

    with pytest.raises(Empty):
        queue.get(timeout=0.05)
