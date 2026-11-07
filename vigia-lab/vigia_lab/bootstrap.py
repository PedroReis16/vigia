"""Prepara o ambiente para usar o código do vigia-onboard SEM alterá-lo.

DEVE ser o primeiro import do `__main__`: fixa variáveis de ambiente antes de
`shared.settings` ser lido e coloca `../vigia-onboard` no `sys.path`.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

LAB_ROOT = Path(__file__).resolve().parents[1]
ONBOARD_ROOT = LAB_ROOT.parent / "vigia-onboard"
LAB_DATA = LAB_ROOT / ".lab-data"


def setup(frame_rate: int = 12, slider_window: int = 30) -> None:
    """Idempotente. Não sobrescreve variáveis já definidas pelo usuário."""
    if not ONBOARD_ROOT.is_dir():
        raise RuntimeError(f"vigia-onboard não encontrado em {ONBOARD_ROOT}")
    LAB_DATA.mkdir(exist_ok=True)
    os.environ.setdefault("DATA_DIR", str(LAB_DATA))
    os.environ.setdefault("FRAME_RATE", str(frame_rate))
    os.environ.setdefault("SLIDER_WINDOW", str(slider_window))
    if str(ONBOARD_ROOT) not in sys.path:
        sys.path.insert(0, str(ONBOARD_ROOT))


def verify_onboard_origin() -> None:
    """Garante que capture/core/shared vieram do onboard (e não de outro lugar)."""
    import capture
    import core
    import shared

    for module in (capture, core, shared):
        origin = Path(module.__file__).resolve()
        if ONBOARD_ROOT not in origin.parents:
            raise RuntimeError(f"{module.__name__} carregado de {origin}, esperado {ONBOARD_ROOT}")
