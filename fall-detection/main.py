"""
Ponto de entrada: uma aplicação, código em `src/app/` (config, capture, ml, …).

Na raiz de fall-detection:

  python main.py

Ou: PYTHONPATH=src python -m app
"""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent
_SRC = _ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from app.config import Settings
from app.runtime import run


def main() -> None:
    run(Settings.from_env())


if __name__ == "__main__":
    main()
