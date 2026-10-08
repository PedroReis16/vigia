"""
Biblioteca de streaming, clipes e thumbnails do onboard.

O capture sobe Processes filhos isolados: RTMP e janela de clips sob demanda,
e thumbnails durante toda a sessão. O arranque/paragem corre numa thread de
supervisão — nunca no loop YOLO.
Não é um serviço Make — use via ``start_supervisor`` / ``stop_supervisor``.
"""

from __future__ import annotations

import logging
import threading
import time
from multiprocessing import Event, Process
from typing import Any

from stream.mp_compat import prepare_multiprocessing, stop_child_process

logger = logging.getLogger(__name__)

_RESTART_BACKOFF_S = 2.0
_SUPERVISE_POLL_S = 0.2

_stream_task: Process | None = None
_clips_task: Process | None = None
_thumbs_task: Process | None = None
_stream_run: Event | None = None
_clips_run: Event | None = None
_thumbs_run: Event | None = None
_stream_backoff_until = 0.0
_clips_backoff_until = 0.0
_thumbs_backoff_until = 0.0
_export_live = False
_capture_fps: int | None = None
_supervisor: threading.Thread | None = None
_supervisor_stop = threading.Event()

__all__ = [
    "ensure_clips_worker",
    "ensure_stream_worker",
    "ensure_thumbs_worker",
    "export_active",
    "prepare_multiprocessing",
    "run_clips_worker",
    "run_stream_worker",
    "run_thumbs_worker",
    "start_supervisor",
    "stop_clips_worker",
    "stop_stream_worker",
    "stop_thumbs_worker",
    "stop_all_workers",
    "stop_supervisor",
    "supervise_workers",
]


def __getattr__(name: str) -> Any:
    if name == "run_stream_worker":
        from stream.stream_runner import run_stream_worker

        return run_stream_worker
    if name == "run_clips_worker":
        from stream.clips_runner import run_clips_worker

        return run_clips_worker
    if name == "run_thumbs_worker":
        from stream.thumbs_runner import run_thumbs_worker

        return run_thumbs_worker
    raise AttributeError(f"module {__name__!r} has no attribute {name}")


def export_active() -> bool:
    """True se o capture deve escrever o frame na live SHM (sem ler ControlShm)."""
    return _export_live


def ensure_stream_worker(live_shm_name: str) -> Process:
    """Garante um Process de stream vivo; devolve a tarefa."""
    global _stream_task, _stream_run
    if _stream_task is not None and _stream_task.is_alive():
        return _stream_task

    from stream.stream_runner import run_stream_worker

    prepare_multiprocessing()
    if _stream_run is None:
        _stream_run = Event()
    _stream_run.set()
    task = Process(
        target=run_stream_worker,
        args=(live_shm_name, _stream_run),
        name="stream",
        daemon=True,
    )
    task.start()
    _stream_task = task
    logger.info("Stream Process iniciado pid=%s", task.pid)
    return task


def ensure_clips_worker(
    live_shm_name: str,
    clip_shm_name: str | None = None,
    *,
    capture_fps: int | None = None,
) -> Process:
    """Garante um Process de clips vivo; devolve a tarefa."""
    global _clips_task, _clips_run
    if _clips_task is not None and _clips_task.is_alive():
        return _clips_task

    from stream.clips_runner import run_clips_worker

    prepare_multiprocessing()
    if _clips_run is None:
        _clips_run = Event()
    _clips_run.set()
    task = Process(
        target=run_clips_worker,
        args=(live_shm_name, clip_shm_name, _clips_run, capture_fps),
        name="clips",
        daemon=True,
    )
    task.start()
    _clips_task = task
    logger.info("Clips Process iniciado pid=%s", task.pid)
    return task


def ensure_thumbs_worker(live_shm_name: str) -> Process:
    """Garante um Process de thumbnail vivo; devolve a tarefa."""
    global _thumbs_task, _thumbs_run
    if _thumbs_task is not None and _thumbs_task.is_alive():
        return _thumbs_task

    from stream.thumbs_runner import run_thumbs_worker

    prepare_multiprocessing()
    if _thumbs_run is None:
        _thumbs_run = Event()
    _thumbs_run.set()
    task = Process(
        target=run_thumbs_worker,
        args=(live_shm_name, _thumbs_run),
        name="thumbs",
        daemon=True,
    )
    task.start()
    _thumbs_task = task
    logger.info("Thumbs Process iniciado pid=%s", task.pid)
    return task


def stop_stream_worker(*, join_timeout: float = 5.0) -> None:
    """Para o Process de stream se existir."""
    global _stream_task
    if _stream_run is not None:
        _stream_run.clear()
    stop_child_process(_stream_task, join_timeout=join_timeout)
    _stream_task = None


def stop_clips_worker(*, join_timeout: float = 5.0) -> None:
    """Para o Process de clips se existir."""
    global _clips_task
    if _clips_run is not None:
        _clips_run.clear()
    stop_child_process(_clips_task, join_timeout=join_timeout)
    _clips_task = None


def stop_thumbs_worker(*, join_timeout: float = 5.0) -> None:
    """Para o Process de thumbnails se existir."""
    global _thumbs_task
    if _thumbs_run is not None:
        _thumbs_run.clear()
    stop_child_process(_thumbs_task, join_timeout=join_timeout)
    _thumbs_task = None


def stop_all_workers(*, join_timeout: float = 5.0) -> None:
    """Para stream, clips e thumbnails."""
    global _stream_backoff_until, _clips_backoff_until, _thumbs_backoff_until
    global _export_live, _capture_fps
    stop_stream_worker(join_timeout=join_timeout)
    stop_clips_worker(join_timeout=join_timeout)
    stop_thumbs_worker(join_timeout=join_timeout)
    _stream_backoff_until = 0.0
    _clips_backoff_until = 0.0
    _thumbs_backoff_until = 0.0
    _export_live = False
    _capture_fps = None


def supervise_workers(
    live_shm_name: str,
    *,
    stream_on: bool,
    clips_enabled: bool,
    clip_shm_name: str | None = None,
    live_shm: Any | None = None,
    capture_fps: int | None = None,
) -> None:
    """
    Sobe/para Processes conforme flags (chamado periodicamente pelo capture).

    Se ``live_shm`` for passado e o stream for parado sem clips activos,
    faz ``reset_sequence`` para invalidar frames stale. O processo de
    thumbnails fica sempre ligado e mantém a escrita na live SHM.
    """
    global _stream_task, _clips_task, _thumbs_task, _export_live
    global _stream_backoff_until, _clips_backoff_until, _thumbs_backoff_until

    _export_live = True
    now = time.monotonic()
    stream_alive = _stream_task is not None and _stream_task.is_alive()
    clips_alive = _clips_task is not None and _clips_task.is_alive()
    thumbs_alive = _thumbs_task is not None and _thumbs_task.is_alive()

    if stream_on and not stream_alive:
        if now >= _stream_backoff_until:
            if _stream_task is not None:
                _stream_backoff_until = now + _RESTART_BACKOFF_S
            if live_shm is not None:
                live_shm.reset_sequence()
            ensure_stream_worker(live_shm_name)
    elif not stream_on and stream_alive:
        stop_stream_worker()
        _stream_backoff_until = 0.0
        if live_shm is not None and not clips_enabled and not thumbs_alive:
            live_shm.reset_sequence()

    if clips_enabled and not clips_alive:
        if now >= _clips_backoff_until:
            if _clips_task is not None:
                _clips_backoff_until = now + _RESTART_BACKOFF_S
            ensure_clips_worker(
                live_shm_name,
                clip_shm_name,
                capture_fps=capture_fps,
            )
    elif not clips_enabled and clips_alive:
        stop_clips_worker()
        _clips_backoff_until = 0.0
        if live_shm is not None and not stream_on and not thumbs_alive:
            live_shm.reset_sequence()

    if not thumbs_alive and now >= _thumbs_backoff_until:
        if _thumbs_task is not None:
            _thumbs_backoff_until = now + _RESTART_BACKOFF_S
        ensure_thumbs_worker(live_shm_name)


def start_supervisor(
    live_shm_name: str,
    clip_shm_name: str | None = None,
    live_shm: Any | None = None,
    capture_fps: int | None = None,
) -> None:
    """Thread que espelha ControlShm e sobe/para os Processes fora do loop YOLO."""
    global _supervisor, _capture_fps, _export_live
    if capture_fps is not None and int(capture_fps) > 0:
        _capture_fps = max(1, int(capture_fps))
    if _supervisor is not None and _supervisor.is_alive():
        return

    _export_live = True
    _supervisor_stop.clear()

    def _loop() -> None:
        from shared.stream_control import get_clips_enabled, get_stream_on

        while not _supervisor_stop.is_set():
            try:
                supervise_workers(
                    live_shm_name,
                    stream_on=get_stream_on(),
                    clips_enabled=get_clips_enabled(),
                    clip_shm_name=clip_shm_name,
                    live_shm=live_shm,
                    capture_fps=_capture_fps,
                )
            except Exception:
                logger.exception("Falha ao supervisionar stream/clips/thumbs")
            _supervisor_stop.wait(_SUPERVISE_POLL_S)

    _supervisor = threading.Thread(target=_loop, name="stream-supervisor", daemon=True)
    _supervisor.start()


def stop_supervisor(*, join_timeout: float = 2.0) -> None:
    """Para a thread de supervisão e os Processes filhos."""
    global _supervisor, _export_live
    _supervisor_stop.set()
    thread = _supervisor
    _supervisor = None
    if thread is not None and thread.is_alive():
        thread.join(timeout=join_timeout)
    _export_live = False
    stop_all_workers()
