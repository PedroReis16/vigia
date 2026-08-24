"""Testes de IPC com start method spawn (Windows/macOS) e helpers cross-platform."""

from __future__ import annotations

import multiprocessing as mp
from unittest.mock import MagicMock, patch

import numpy as np

from integration.fall_ipc import enqueue_fall_state, init_fall_queue
from streaming.frame_ipc import get_frame, put_frame
from streaming import mp_compat
from streaming import rtmp as rtmp_mod


def _spawn_put_frame(queue, value: int) -> None:
    """Target picklável para Process(spawn)."""
    frame = np.full((2, 2, 3), value, dtype=np.uint8)
    put_frame(queue, frame)


def _spawn_enqueue_fall(queue, label: str) -> None:
    """Target picklável: string via fall_queue entre processos."""
    init_fall_queue(queue)
    enqueue_fall_state(label)


def _spawn_read_event(event, result_queue) -> None:
    result_queue.put(bool(event.is_set()))


def test_ipc_put_get_ComContextoSpawn_PreservaFrame() -> None:
    ctx = mp.get_context("spawn")
    queue = ctx.Queue(maxsize=2)
    proc = ctx.Process(target=_spawn_put_frame, args=(queue, 7))
    proc.start()
    proc.join(timeout=15)
    assert proc.exitcode == 0

    restored = get_frame(queue, timeout=5.0)
    assert restored is not None
    np.testing.assert_array_equal(restored, np.full((2, 2, 3), 7, dtype=np.uint8))


def test_fall_queue_ComContextoSpawn_PreservaString() -> None:
    ctx = mp.get_context("spawn")
    queue = ctx.Queue(maxsize=8)
    proc = ctx.Process(target=_spawn_enqueue_fall, args=(queue, "fall"))
    proc.start()
    proc.join(timeout=15)
    assert proc.exitcode == 0
    assert queue.get(timeout=5.0) == "fall"


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
    queue = MagicMock()
    queue.get_nowait.side_effect = Exception("empty")  # type: ignore[attr-defined]

    # drain_queue captura Empty — simular fila já vazia via patch
    with patch.object(mp_compat, "drain_queue") as mock_drain:
        mp_compat.stop_child_process(task, frame_queue=queue, join_timeout=0.1)

    task.join.assert_called()
    task.terminate.assert_not_called()
    mock_drain.assert_called_once_with(queue)


def test_stop_child_process_AindaVivo_UsaTerminate() -> None:
    task = MagicMock()
    task.is_alive.return_value = True

    with patch.object(mp_compat, "drain_queue"):
        mp_compat.stop_child_process(task, frame_queue=None, join_timeout=0.01)

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
        publisher.start(64, 48, 12, "rtmp://localhost/live/dev")

    kwargs = mock_popen.call_args.kwargs
    assert "close_fds" not in kwargs
    assert kwargs["stdin"] is rtmp_mod.subprocess.PIPE
