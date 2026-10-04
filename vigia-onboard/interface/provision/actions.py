"""Acções locais: Wi-Fi, reset de utilizador e gate da captura."""

from __future__ import annotations

import logging
import os
import shutil
import subprocess
from pathlib import Path

from shared.capture_gate import (
    capture_is_active as _capture_is_active,
    hold_capture,
    release_capture,
    request_capture_restart,
)

from .identity import is_provisioned
from .settings import get_network_path, get_settings
from .state import request_force_pairing, request_pairing_restart
from .sysenv import system_subprocess_env

log = logging.getLogger(__name__)

RESET_SCRIPT = os.getenv("VIGIA_RESET_SCRIPT", "/usr/local/bin/vigia_reset_config.sh")
WIFI_RESET_SCRIPT = os.getenv(
    "VIGIA_RESET_WIFI_SCRIPT", "/usr/local/bin/vigia_reset_wifi.sh"
)


def capture_is_active() -> bool:
    """True se a captura escreveu um PID ainda vivo."""
    return _capture_is_active()


def stop_capture() -> None:
    """Bloqueia a captura (capture.hold) em vez de systemctl stop."""
    hold_capture()
    log.info("Captura bloqueada (capture.hold)")


def restart_capture() -> None:
    """Abre o gate e pede nova sessão para reler classifier.json."""
    release_capture()
    request_capture_restart()
    log.info("Pedido de restart da captura")


def _clear_capture_local_data() -> None:
    """Remove dados runtime locais; preserva identity.json e network.json."""
    root = Path(get_settings().data_dir)
    for rel in ("fall-detection/data", "onboard/data", "DB", "data"):
        path = root / rel
        if path.is_dir():
            shutil.rmtree(path, ignore_errors=True)
            log.info("Removido %s", path)
        elif path.is_file():
            path.unlink(missing_ok=True)


def clear_wifi() -> None:
    """Apaga só network.json e bloqueia a captura (mantém identidade)."""
    script = WIFI_RESET_SCRIPT
    if os.path.isfile(script) and os.access(script, os.X_OK):
        subprocess.run([script], check=False, env=system_subprocess_env())
    else:
        stop_capture()
        path = get_network_path()
        if path.exists():
            path.unlink()
            log.info("network.json removido")
        if is_provisioned():
            log.warning("clear_wifi: identity+network ainda presentes")
    request_pairing_restart()


def unlink_user() -> None:
    """Desvincula utilizador: bloqueia a captura e mantém rede/identidade."""
    script = RESET_SCRIPT
    if os.path.isfile(script) and os.access(script, os.X_OK):
        subprocess.run([script], check=False, env=system_subprocess_env())
    else:
        stop_capture()
        _clear_capture_local_data()
        log.info("unlink_user: fallback sem script — rede e identidade preservadas")
    request_force_pairing()
