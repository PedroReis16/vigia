"""Orquestra pareamento BLE e arranque do fall-detection."""

from __future__ import annotations

import asyncio
import logging
import subprocess
import threading

from .identity import is_provisioned, load_or_create_identity
from .state import set_phase

log = logging.getLogger(__name__)

FALL_SERVICE = "fall-detection.service"


def start_fall_detection() -> None:
    result = subprocess.run(
        ["systemctl", "start", FALL_SERVICE],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        log.warning(
            "Não foi possível iniciar %s: %s",
            FALL_SERVICE,
            (result.stderr or result.stdout or "").strip(),
        )
    else:
        log.info("Pedido de start enviado a %s", FALL_SERVICE)


async def provision_supervisor(cancel: threading.Event) -> None:
    """
    Se identity+network existem, arranca o fall e vigia um reset.
    Caso contrário abre o beacon até o app provisionar (ou cancel).
    """
    while True:
        if cancel.is_set():
            cancel.clear()
            set_phase("idle")
            await asyncio.sleep(0.2)
            continue

        if is_provisioned():
            set_phase("ready")
            start_fall_detection()
            log.info("Dispositivo já provisionado — a aguardar reset")
            while is_provisioned() and not cancel.is_set():
                await asyncio.sleep(1)
            continue

        identity = load_or_create_identity()
        set_phase("pairing")
        log.info("A iniciar pareamento BLE para %s", identity.device_name)
        from .ble import init_register_beacon

        await init_register_beacon(
            identity.device_id,
            identity.device_name,
            identity.mac_address,
            identity.sign_priv,
            identity.ecdh_priv,
            cancel=cancel,
        )

        if is_provisioned() and not cancel.is_set():
            set_phase("ready")
            start_fall_detection()
        else:
            set_phase("idle")
