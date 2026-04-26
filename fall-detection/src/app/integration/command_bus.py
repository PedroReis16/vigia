from __future__ import annotations

import os
from pathlib import Path

import aiohttp

from app.integration.types import CommandHandler, IntegrationContext
from app.logging import get_logger

_CUSTOM_HANDLERS: dict[str, CommandHandler] = {}
logger = get_logger("integration")


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


async def _default_stream_handler(_: dict) -> None:
    logger.info("comando stream recebido (acionar modulo capture)")


async def _default_restart_core_handler(_: dict) -> None:
    logger.info("comando restart_core recebido (reiniciar modulo core)")


def build_dispatcher(context: IntegrationContext) -> CommandDispatcher:
    dispatcher = CommandDispatcher(context)
    dispatcher.register("stream", _default_stream_handler)
    dispatcher.register("restart_core", _default_restart_core_handler)
    dispatcher.register("upload_logs", _upload_logs_async)
    for command_name, handler in _CUSTOM_HANDLERS.items():
        dispatcher.register(command_name, handler)
    return dispatcher
