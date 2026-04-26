"""
Ponto de entrada: ``python -m app.core``.

Use ``pip install -e .`` na raiz do projeto ou ``cd src`` para o ``-m`` encontrar o pacote.
"""

from __future__ import annotations

from app.path_setup import ensure_src_on_path

ensure_src_on_path()

from app.config import Settings
from app.core.runner import run_analysis
from app.logging import configure_logging


def main() -> None:
    configure_logging()
    run_analysis(Settings.from_env())


if __name__ == "__main__":
    main()
