"""
Ponto de entrada na raiz do projeto fall-detection.

  python main.py

Ou, após ``pip install -e .`` na raiz::

  python -m app

Ou, sem instalar o pacote::

  cd src && python -m app
"""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent
_SRC = _ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from app.path_setup import ensure_src_on_path

ensure_src_on_path()

from app.config import Settings
from app.runtime import run


def main() -> None:
    run(Settings.from_env())


if __name__ == "__main__":
    from multiprocessing import freeze_support

    freeze_support()
    main()
