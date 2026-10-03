"""Caminhos do onboard (raiz, venv, requirements) e dos serviços."""

from __future__ import annotations

import sys
from pathlib import Path


def onboard_root() -> Path:
    """Raiz do onboard (Makefile e `.env` central)."""
    return Path(__file__).resolve().parents[1]


def capture_root() -> Path:
    """Raiz do serviço de captura (`capture/`)."""
    return onboard_root() / "capture"


def core_root() -> Path:
    """Raiz do pacote de classificação (`core/`)."""
    return onboard_root() / "core"


def integration_root() -> Path:
    """Raiz do serviço de integração (`integration/`)."""
    return onboard_root() / "integration"


def venv_dir() -> Path:
    """Virtualenv partilhado do onboard (`.venv` na raiz)."""
    return onboard_root() / ".venv"


def requirements_file() -> Path:
    """`requirements.txt` central do onboard."""
    return onboard_root() / "requirements.txt"


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
