"""
Ponto de entrada: ``python -m app``.

Na raiz do repositório, use ``pip install -e .`` (recomendado) ou ``cd src`` antes do ``-m``.
"""

from __future__ import annotations

from app.path_setup import ensure_src_on_path

ensure_src_on_path()

from app.config import Settings
from app.runtime import run


def main() -> None:
    """Configuração via ambiente e execução do runtime."""
    run(Settings.from_env())


if __name__ == "__main__":
    from multiprocessing import freeze_support

    freeze_support()
    main()
