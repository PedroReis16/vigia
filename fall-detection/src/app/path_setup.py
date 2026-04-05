"""Garante que o diretório `src/` está em sys.path (layout com pacote em `src/app/`)."""

from __future__ import annotations

import sys
from pathlib import Path


def ensure_src_on_path() -> None:
    """Idempotente: insere o pai do pacote `app` em sys.path se ainda não estiver."""
    src_root = Path(__file__).resolve().parent.parent
    s = str(src_root)
    if s not in sys.path:
        sys.path.insert(0, s)
