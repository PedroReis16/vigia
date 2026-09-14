"""Ambiente limpo para invocar binários do sistema a partir do bundle PyInstaller."""

from __future__ import annotations

import os
import sys

_BUNDLE_PATH_MARKERS = ("/_internal", "_internal/")


def _is_bundle_lib_path(path: str) -> bool:
    if not path:
        return False
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass and (path == meipass or path.startswith(f"{meipass}/")):
        return True
    return any(marker in path for marker in _BUNDLE_PATH_MARKERS)


def _scrub_path_env(value: str) -> str | None:
    parts = [p for p in value.split(":") if p and not _is_bundle_lib_path(p)]
    return ":".join(parts) if parts else None


def system_subprocess_env() -> dict[str, str]:
    """
    Ambiente para binários do sistema (systemctl, nmcli, bash, …).

    O bootloader do PyInstaller injeta ``_internal`` em ``LD_LIBRARY_PATH``;
    binários do apt passam a carregar libs do bundle (incompatíveis) e falham.
    Restaura o valor original (``LD_LIBRARY_PATH_ORIG``) ou remove a variável.
    """
    env = os.environ.copy()

    for key in ("LD_LIBRARY_PATH", "LD_PRELOAD", "LIBRARY_PATH"):
        env.pop(f"{key}_ORIG", None)
        current = env.get(key)
        if current is None:
            continue
        cleaned = _scrub_path_env(current)
        if cleaned is None:
            env.pop(key, None)
        else:
            env[key] = cleaned

    lp_orig = os.environ.get("LD_LIBRARY_PATH_ORIG")
    if lp_orig is not None:
        cleaned_orig = _scrub_path_env(lp_orig)
        if cleaned_orig is None:
            env.pop("LD_LIBRARY_PATH", None)
        else:
            env["LD_LIBRARY_PATH"] = cleaned_orig
    else:
        env.pop("LD_LIBRARY_PATH", None)

    return env
