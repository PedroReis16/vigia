"""
Configuração centralizada de logging para processos do vigia-fall.
"""

from __future__ import annotations

import logging
import multiprocessing
import os
import sys


class _FlushingStreamHandler(logging.StreamHandler):
    """StreamHandler que faz flush após cada emit (visível sob systemd/pipe)."""

    def emit(self, record: logging.LogRecord) -> None:
        super().emit(record)
        self.flush()


def configure_logging(process_name: str | None = None) -> None:
    """
    Configura o root logger com flush imediato.

    ``LOG_LEVEL`` (default INFO) controla o nível. ``process_name`` atualiza
    o nome do processo atual para aparecer em ``%(processName)s``.
    """
    if process_name:
        multiprocessing.current_process().name = process_name

    level_name = os.getenv("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)
    handler = _FlushingStreamHandler(sys.stdout)
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(processName)s] %(levelname)s %(name)s: %(message)s",
        datefmt="%H:%M:%S",
        handlers=[handler],
        force=True,
    )
