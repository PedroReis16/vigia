"""Entrada do módulo: `python -m interface` na raiz do onboard."""

from __future__ import annotations

import logging
import sys

from shared.paths import interface_root
from shared.runtime import prepare_runtime

logger = logging.getLogger(__name__)


def main() -> int:
    """Prepara o runtime e executa o control plane."""
    args = sys.argv[1:]
    setup_only = "--setup-only" in args
    prepare_runtime(reexec_module="interface", skip_model=True)
    if setup_only:
        logger.info("Runtime do interface inicializado em %s", interface_root())
        return 0

    from interface.interface_runner import run_interface

    logger.info("A executar o interface em %s", interface_root())
    run_interface()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
