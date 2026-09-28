"""Entrada do módulo: `python -m integration` na raiz do onboard."""

from __future__ import annotations

import logging
import sys

from shared.paths import integration_root
from shared.runtime import prepare_runtime

logger = logging.getLogger(__name__)


def main() -> int:
    """Prepara o runtime e executa o loop de integração."""
    args = sys.argv[1:]
    setup_only = "--setup-only" in args
    # Deps (ex.: paho-mqtt) só existem depois do prepare/reexec no venv.
    prepare_runtime(reexec_module="integration", skip_model=True)
    if setup_only:
        logger.info("Runtime do integration inicializado em %s", integration_root())
        return 0

    from integration.integration_runner import run_integration

    logger.info("A executar a integração em %s", integration_root())
    run_integration()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
