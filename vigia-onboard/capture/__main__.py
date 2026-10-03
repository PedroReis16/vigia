"""Entrada do módulo: `python -m capture` na raiz do onboard."""

from __future__ import annotations

import logging
import sys

from shared.paths import capture_root
from shared.runtime import prepare_runtime
from capture.capture_runner import run_capture

logger = logging.getLogger(__name__)


def main() -> int:
    """Prepara o runtime e executa o loop de captura."""
    args = sys.argv[1:]
    skip_model = "--skip-model" in args
    setup_only = "--setup-only" in args
    prepare_runtime(reexec_module="capture", skip_model=skip_model)
    if setup_only:
        logger.info("Runtime do capture inicializado em %s", capture_root())
        return 0

    
    logger.info("A executar a captura em %s", capture_root())
    run_capture()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
