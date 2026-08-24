"""Testes unitários para serialização IPC de frames."""

from multiprocessing import Queue

import numpy as np

from streaming.frame_ipc import drain_queue, get_frame, put_frame


def test_put_get_PreservaConteudoBGR() -> None:
    q: Queue = Queue(maxsize=2)
    original = np.arange(12, dtype=np.uint8).reshape(2, 2, 3)

    put_frame(q, original)
    restored = get_frame(q, timeout=1.0)

    assert restored is not None
    np.testing.assert_array_equal(restored, original)


def test_put_frame_VazioOuNone_Ignora() -> None:
    q: Queue = Queue(maxsize=2)

    put_frame(q, None)  # type: ignore[arg-type]
    put_frame(q, np.array([], dtype=np.uint8))

    assert get_frame(q, timeout=0.05) is None


def test_put_frame_FilaCheia_DescartaMaisAntigo() -> None:
    q: Queue = Queue(maxsize=2)
    first = np.zeros((2, 2, 3), dtype=np.uint8)
    second = np.ones((2, 2, 3), dtype=np.uint8)
    third = np.full((2, 2, 3), 2, dtype=np.uint8)

    put_frame(q, first)
    put_frame(q, second)
    put_frame(q, third)

    a = get_frame(q, timeout=1.0)
    b = get_frame(q, timeout=1.0)

    assert a is not None and b is not None
    np.testing.assert_array_equal(a, second)
    np.testing.assert_array_equal(b, third)
    assert get_frame(q, timeout=0.05) is None


def test_drain_queue_EsvaziaTodosOsItens() -> None:
    q: Queue = Queue(maxsize=2)
    put_frame(q, np.zeros((1, 1, 3), dtype=np.uint8))
    put_frame(q, np.ones((1, 1, 3), dtype=np.uint8))

    drain_queue(q)

    assert get_frame(q, timeout=0.05) is None
