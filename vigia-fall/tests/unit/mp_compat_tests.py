"""Testes de compatibilidade multiprocessing e helpers cross-platform."""

from __future__ import annotations

import multiprocessing as mp
from unittest.mock import MagicMock, patch

import numpy as np

from integration.fall_shm import enqueue_fall_state, init_fall_shm
from shared.event_shm import EventShmRing
from shared.event_types import EVENT_FALL_STATE
from streaming import mp_compat
from streaming import rtmp as rtmp_mod
from streaming.frame_shm import FrameShmRing


def _spawn_write_shm(shm_name: str, value: int) -> None:
    ring = FrameShmRing.attach(shm_name)
    ring.write(np.full((2, 2, 3), value, dtype=np.uint8), 30)
    ring.close()


def _spawn_enqueue_fall(shm_name: str, label: str) -> None:
    init_fall_shm(shm_name)
    enqueue_fall_state(label)


def _spawn_read_event(event, result_queue) -> None:
    result_queue.put(bool(event.is_set()))


def test_shm_write_ComContextoSpawn() -> None:
    owner = FrameShmRing.create(max_payload=64)
    try:
        ctx = mp.get_context("spawn")
        proc = ctx.Process(target=_spawn_write_shm, args=(owner.name, 7))
        proc.start()
        proc.join(timeout=15)
        assert proc.exitcode == 0

        item = owner.read_latest(timeout=1.0)
        assert item is not None
        np.testing.assert_array_equal(item.frame, np.full((2, 2, 3), 7, dtype=np.uint8))
    finally:
        owner.close()
        owner.unlink()


def test_fall_shm_ComContextoSpawn_PreservaString() -> None:
    owner = EventShmRing.create(slot_count=8, payload_max=64)
    try:
        ctx = mp.get_context("spawn")
        proc = ctx.Process(target=_spawn_enqueue_fall, args=(owner.name, "fall"))
        proc.start()
        proc.join(timeout=15)
        assert proc.exitcode == 0

        event = owner.read_next(timeout=5.0)
        assert event is not None
        assert event.event_type == EVENT_FALL_STATE
        assert event.payload == "fall"
    finally:
        owner.close()
        owner.unlink()


def test_event_Compartilhado_ComContextoSpawn() -> None:
    ctx = mp.get_context("spawn")
    event = ctx.Event()
    event.set()
    result_queue = ctx.Queue()
    proc = ctx.Process(target=_spawn_read_event, args=(event, result_queue))
    proc.start()
    proc.join(timeout=15)
    assert proc.exitcode == 0
    assert result_queue.get(timeout=5.0) is True


def test_stop_child_process_JoinAntesDeTerminate() -> None:
    task = MagicMock()
    task.is_alive.side_effect = [True, False]

    mp_compat.stop_child_process(task, join_timeout=0.1)

    task.join.assert_called()
    task.terminate.assert_not_called()


def test_stop_child_process_AindaVivo_UsaTerminate() -> None:
    task = MagicMock()
    task.is_alive.return_value = True

    mp_compat.stop_child_process(task, join_timeout=0.01)

    task.terminate.assert_called_once()


def test_scrub_path_env_UsaPathsepDaPlataforma() -> None:
    import os

    dirty = os.pathsep.join(["/usr/lib", "/tmp/_internal/lib", "/opt/lib"])
    cleaned = rtmp_mod._scrub_path_env(dirty)
    assert cleaned is not None
    assert "_internal" not in cleaned
    assert "/usr/lib" in cleaned
    assert "/opt/lib" in cleaned


def test_ffmpeg_executable_Windows_UsaWhich() -> None:
    with (
        patch.object(rtmp_mod.sys, "platform", "win32"),
        patch.object(rtmp_mod.shutil, "which", return_value=r"C:\ffmpeg\bin\ffmpeg.exe") as mock_which,
    ):
        result = rtmp_mod._ffmpeg_executable()

    assert result == r"C:\ffmpeg\bin\ffmpeg.exe"
    mock_which.assert_any_call("ffmpeg.exe")


def test_ffmpeg_executable_Mac_HomebrewPath() -> None:
    with (
        patch.object(rtmp_mod.sys, "platform", "darwin"),
        patch.object(rtmp_mod.os.path, "isfile", side_effect=lambda p: p == "/opt/homebrew/bin/ffmpeg"),
        patch.object(rtmp_mod.os, "access", return_value=True),
    ):
        result = rtmp_mod._ffmpeg_executable()

    assert result == "/opt/homebrew/bin/ffmpeg"


def test_rtmp_publisher_start_Windows_SemCloseFds() -> None:
    publisher = rtmp_mod.RtmpPublisher()
    fake_proc = MagicMock()
    fake_proc.poll.return_value = None

    with (
        patch.object(rtmp_mod.sys, "platform", "win32"),
        patch.object(rtmp_mod, "_ffmpeg_executable", return_value="ffmpeg"),
        patch.object(rtmp_mod.subprocess, "Popen", return_value=fake_proc) as mock_popen,
    ):
        publisher.start(64, 48, 30, "rtmp://localhost/live/dev")

    kwargs = mock_popen.call_args.kwargs
    assert "close_fds" not in kwargs
    assert kwargs["stdin"] is rtmp_mod.subprocess.PIPE


def test_publish_frame_ChamaPublisher() -> None:
    frame = np.zeros((4, 4, 3), dtype=np.uint8)
    with (
        patch.object(rtmp_mod, "_publisher") as mock_pub,
        patch.object(rtmp_mod, "_resolve_target", return_value=(30, "rtmp://x")),
    ):
        rtmp_mod.publish_frame(frame, 30)

    mock_pub.start.assert_called_once()
    mock_pub.write.assert_called_once()
