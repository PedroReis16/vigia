"""Código partilhado entre os serviços Python do onboard.

Helpers de settings/provisionamento são importados sob demanda para
`python -m <módulo>` correr no Python do host (sem python-dotenv) antes de
reabrir o .venv.
"""

from __future__ import annotations

from typing import Any

__all__ = [
    "get_settings",
    "get_device_identity",
    "get_network_settings",
    "get_classifier_path",
    "resolve_ota_dir",
    "resolve_install_root",
]


def __getattr__(name: str) -> Any:
    if name in __all__:
        from . import settings as _settings

        return getattr(_settings, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
