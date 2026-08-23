"""Acções locais: Wi‑Fi, reset de utilizador, serviço fall."""

from __future__ import annotations

import logging
import os
import subprocess

from .identity import is_provisioned
from .settings import get_network_path
from .state import request_pairing_restart
from .sysenv import system_subprocess_env

log = logging.getLogger(__name__)

FALL_SERVICE = "fall-detection.service"
RESET_SCRIPT = os.getenv("VIGIA_RESET_SCRIPT", "/usr/local/bin/vigia_reset_config.sh")
WIFI_RESET_SCRIPT = os.getenv(
    "VIGIA_RESET_WIFI_SCRIPT", "/usr/local/bin/vigia_reset_wifi.sh"
)


def stop_fall_detection() -> None:
    subprocess.run(
        ["systemctl", "stop", FALL_SERVICE],
        capture_output=True,
        text=True,
        check=False,
        env=system_subprocess_env(),
    )


def restart_fall_detection() -> None:
    result = subprocess.run(
        ["systemctl", "restart", FALL_SERVICE],
        capture_output=True,
        text=True,
        check=False,
        env=system_subprocess_env(),
    )
    if result.returncode != 0:
        log.warning("restart %s falhou: %s", FALL_SERVICE, result.stderr.strip())


def fall_is_active() -> bool:
    try:
        result = subprocess.run(
            ["systemctl", "is-active", FALL_SERVICE],
            capture_output=True,
            text=True,
            check=False,
            timeout=1,
            env=system_subprocess_env(),
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    return result.stdout.strip() == "active"


def clear_wifi() -> None:
    """Apaga só network.json e pára o fall (mantém identidade)."""
    script = WIFI_RESET_SCRIPT
    if os.path.isfile(script) and os.access(script, os.X_OK):
        subprocess.run([script], check=False, env=system_subprocess_env())
    else:
        stop_fall_detection()
        path = get_network_path()
        if path.exists():
            path.unlink()
            log.info("network.json removido")
        if is_provisioned():
            log.warning("clear_wifi: identity+network ainda presentes")
    request_pairing_restart()


def unlink_user() -> None:
    subprocess.run([RESET_SCRIPT], check=False, env=system_subprocess_env())
    request_pairing_restart()
