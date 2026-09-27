"""Processo core do onboard (consumo da captura)."""

from __future__ import annotations

import logging
import time

logger = logging.getLogger(__name__)


def run_core() -> None:
    """Mantém o processo vivo até CTRL+C. A lógica de consumo entra aqui."""
    logger.info("Core inicializado")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Core encerrado")
