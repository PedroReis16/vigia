"""
Ponto de entrada: ``python -m app.capture``.

Use ``pip install -e .`` na raiz do projeto ou ``cd src`` para o ``-m`` encontrar o pacote.
"""

from __future__ import annotations

from app.path_setup import ensure_src_on_path

ensure_src_on_path()

from app.config import Settings
from app.capture.runner import run_capture


def main() -> None:
    run_capture(Settings.from_env())


if __name__ == "__main__":
    main()
