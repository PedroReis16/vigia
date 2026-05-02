from __future__ import annotations

import asyncio
import os
from multiprocessing import Process, get_context
from pathlib import Path

import aiohttp

from app.config import Settings
from app.integration.types import CommandHandler, IntegrationContext
from app.logging import get_logger

_CUSTOM_HANDLERS: dict[str, CommandHandler] = {}
logger = get_logger("integration")

# spawn evita fork com asyncio (macOS); mesmo contexto para arranque do streaming.
_spawn_ctx = get_context("spawn")

_streaming_process: Process | None = None
_streaming_lock = asyncio.Lock()


def _payload_requests_stream_stop(payload: dict) -> bool:
    v = str(payload.get("value", "")).strip().lower()
    return v in ("0", "false", "off", "stop", "no")


def _run_streaming_worker(settings: Settings) -> None:
    """Import pesado (numpy/OpenCV) só no processo filho."""
    from app.streaming.runner import run_streaming

    run_streaming(settings)


async def _stop_streaming_subprocess() -> None:
    global _streaming_process
    proc = _streaming_process
    if proc is None:
        logger.info("streaming ja estava parado")
        return
    if not proc.is_alive():
        _streaming_process = None
        return
    proc.terminate()

    def _join_and_force_kill() -> None:
        proc.join(timeout=15)
        if proc.is_alive():
            logger.warning(
                "processo streaming nao terminou apos SIGTERM; enviando kill (pid={})",
                proc.pid,
            )
            proc.kill()
            proc.join(timeout=8)

    await asyncio.to_thread(_join_and_force_kill)
    _streaming_process = None
    logger.info("streaming encerrado")


class CommandDispatcher:
    def __init__(self, context: IntegrationContext) -> None:
        self.context = context
        self._handlers: dict[str, CommandHandler] = {}

    def register(self, command_name: str, handler: CommandHandler) -> None:
        self._handlers[command_name.lower()] = handler

    async def dispatch(self, command_name: str, payload: dict) -> None:
        command = command_name.lower()
        handler = self._handlers.get(command)
        if handler is None:
            logger.warning("comando nao suportado: {}", command_name)
            return
        await handler(payload)


def register_command_handler(command_name: str, handler: CommandHandler) -> None:
    """Permite aos demais modulos registrar tratadores de comando."""
    _CUSTOM_HANDLERS[command_name.lower()] = handler


async def _upload_logs_async(payload: dict) -> None:
    logs_api_url = (os.getenv("LOGS_API_URL") or "").strip()
    if not logs_api_url:
        logger.warning("LOGS_API_URL nao configurada; upload de logs ignorado")
        return

    logs_path = Path((payload.get("path") or "logs/app.log")).resolve()
    if not logs_path.exists() or not logs_path.is_file():
        logger.warning("arquivo de log nao encontrado: {}", logs_path)
        return

    async with aiohttp.ClientSession() as session:
        with logs_path.open("rb") as log_file:
            form = aiohttp.FormData()
            form.add_field("logfile", log_file, filename=logs_path.name)
            async with session.post(logs_api_url, data=form, timeout=60) as response:
                if response.status not in (200, 201, 202):
                    raise Exception(
                        f"falha upload logs: {response.status} {await response.text()}"
                    )

    logger.info("upload de logs concluido: {}", logs_path.name)


async def _default_restart_core_handler(_: dict) -> None:
    logger.info("comando restart_core recebido (reiniciar modulo core)")


def build_dispatcher(context: IntegrationContext) -> CommandDispatcher:
    dispatcher = CommandDispatcher(context)

    async def stream_handler(payload: dict) -> None:
        """
        Inicia ou para o processo de streaming (RTMP) que consome frames ZMQ.
        Payload FIWARE/UL: value em off/false/0/stop para parar; vazio ou on para iniciar.
        Requer captura a correr (``python -m app``) para haver frames em ipc:///tmp/frames.ipc.
        """
        global _streaming_process

        if _payload_requests_stream_stop(payload):
            async with _streaming_lock:
                await _stop_streaming_subprocess()
            return

        settings = context.settings
        if not (settings.stream_ingest_url or "").strip():
            logger.warning(
                "comando stream ignorado: STREAM_INGEST_URL nao configurada no ambiente"
            )
            return

        async with _streaming_lock:
            if _streaming_process is not None and _streaming_process.is_alive():
                logger.info("streaming ja em execucao; ignorando comando duplicado")
                return

            proc = _spawn_ctx.Process(
                target=_run_streaming_worker,
                args=(settings,),
                name="vigia-streaming",
            )
            proc.start()
            _streaming_process = proc
            logger.info("processo de streaming iniciado (pid={})", proc.pid)

    dispatcher.register("stream", stream_handler)
    dispatcher.register("restart_core", _default_restart_core_handler)
    dispatcher.register("upload_logs", _upload_logs_async)
    for command_name, handler in _CUSTOM_HANDLERS.items():
        dispatcher.register(command_name, handler)
    return dispatcher
