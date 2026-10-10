"""Testes do ControlShm (stream_on / clips_enabled / blur_enabled)."""

from __future__ import annotations

import uuid

import pytest

from shared import stream_control as sc


@pytest.fixture(autouse=True)
def _unique_control_name(monkeypatch: pytest.MonkeyPatch):
    # macOS PSEMNAMLEN ~31; nomes longos falham com Errno 63.
    name = f"vtc{uuid.uuid4().hex[:12]}"
    monkeypatch.setattr(
        sc,
        "get_settings",
        lambda: type("S", (), {"stream_control_shm_name": name})(),
    )
    sc.reset_stream_control_for_tests()
    yield name
    sc.reset_stream_control_for_tests()


def test_flags_default_false(_unique_control_name: str) -> None:
    assert sc.get_stream_on() is False
    assert sc.get_clips_enabled() is False
    assert sc.get_blur_enabled() is False


def test_set_stream_preserva_clips(_unique_control_name: str) -> None:
    sc.set_clips_enabled(True)
    sc.set_stream_status(True)
    assert sc.get_stream_on() is True
    assert sc.get_clips_enabled() is True
    sc.set_stream_status(False)
    assert sc.get_stream_on() is False
    assert sc.get_clips_enabled() is True


def test_set_clips_preserva_stream(_unique_control_name: str) -> None:
    sc.set_stream_status(True)
    sc.set_clips_enabled(True)
    sc.set_clips_enabled(False)
    assert sc.get_stream_on() is True
    assert sc.get_clips_enabled() is False


def test_set_blur_preserva_stream_e_clips(_unique_control_name: str) -> None:
    sc.set_stream_status(True)
    sc.set_clips_enabled(True)
    sc.set_blur_enabled(True)
    sc.set_stream_status(False)
    sc.set_clips_enabled(False)
    assert sc.get_blur_enabled() is True
    sc.set_blur_enabled(False)
    assert sc.get_stream_on() is False
    assert sc.get_clips_enabled() is False
    assert sc.get_blur_enabled() is False


def test_recria_segmento_menor_que_o_cabecalho(_unique_control_name: str) -> None:
    from multiprocessing.shared_memory import SharedMemory

    stale = SharedMemory(name=_unique_control_name, create=True, size=2)
    reported = stale.size
    stale.buf[0] = 1
    stale.buf[1] = 1
    stale.close()

    assert sc.get_blur_enabled() is False
    sc.set_blur_enabled(True)
    assert sc.get_blur_enabled() is True
    if reported < sc._HEADER_SIZE:
        assert sc.get_stream_on() is False
        assert sc.get_clips_enabled() is False
    else:
        assert sc.get_stream_on() is True
        assert sc.get_clips_enabled() is True
