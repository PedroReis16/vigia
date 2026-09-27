"""Entrada do módulo: `python -m core` na raiz do onboard."""

from __future__ import annotations

import logging
import sys

from shared.paths import onboard_root
from shared.runtime import prepare_runtime

logger = logging.getLogger(__name__)


def main() -> int:
    """Prepara o runtime e executa o core."""
    setup_only = "--setup-only" in sys.argv[1:]
    prepare_runtime(reexec_module="core", skip_model=True)
    if setup_only:
        logger.info("Runtime do core inicializado em %s", onboard_root())
        return 0

    from core.runner import run_core

    run_core()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
