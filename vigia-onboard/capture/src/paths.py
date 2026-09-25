"""Caminhos do serviço capture (raiz, venv, requirements)."""

from __future__ import annotations

import sys
from pathlib import Path


def capture_root() -> Path:
    """Raiz do serviço (`capture/`)."""
    return Path(__file__).resolve().parents[1]


def onboard_root() -> Path:
    """Raiz do onboard (onde estão o Makefile e o `.env` central)."""
    return capture_root().parent


def venv_dir() -> Path:
    """Virtualenv do capture (`capture/.venv`)."""
    return capture_root() / ".venv"


def requirements_file() -> Path:
    return capture_root() / "requirements.txt"


def venv_python(venv: Path | None = None) -> Path:
    """Interpretador do venv (bin/ no Unix, Scripts/ no Windows)."""
    root = venv if venv is not None else venv_dir()
    if sys.platform == "win32":
        return root / "Scripts" / "python.exe"
    return root / "bin" / "python"


def is_running_in_venv(venv: Path | None = None) -> bool:
    """True se o interpretador atual for o do venv do capture."""
    root = (venv if venv is not None else venv_dir()).resolve()
    return Path(sys.prefix).resolve() == root
