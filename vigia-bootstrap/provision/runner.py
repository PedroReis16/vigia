"""Orquestra pareamento BLE e arranque do fall-detection."""

from __future__ import annotations

import asyncio
import logging
import subprocess
import threading

from .ble import ble_unavailable_reason, init_register_beacon, is_ble_available
from .classifier import ensure_classifier_config
from .identity import is_provisioned, load_or_create_identity
from .state import clear_force_pairing, is_force_pairing, set_phase
from .sysenv import system_subprocess_env
from .wifi import ensure_mock_network

log = logging.getLogger(__name__)

FALL_SERVICE = "fall-detection.service"


async def _wait_pairing_without_ble(cancel: threading.Event) -> None:
    """Mantém o supervisor vivo em debug sem stack BLE (menu/UI continuam)."""
    log.warning(
        "%s — UI/menu continuam; use identity+network.json ou active BLE no deploy",
        ble_unavailable_reason(),
    )
    while not cancel.is_set() and not is_provisioned():
        await asyncio.sleep(1)


def start_fall_detection() -> None:
    try:
        result = subprocess.run(
            ["systemctl", "start", FALL_SERVICE],
            capture_output=True,
            text=True,
            check=False,
            env=system_subprocess_env(),
        )
    except FileNotFoundError:
        log.warning(
            "systemctl indisponível — %s não arrancado (normal em dev local)",
            FALL_SERVICE,
        )
        return
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
    Se identity+network existem (e sem force pairing), arranca o fall.
    Caso contrário — ou após Desvincular — abre o beacon BLE.
    """
    while True:
        if cancel.is_set():
            cancel.clear()
            set_phase("idle")
            await asyncio.sleep(0.2)
            continue

        if is_provisioned() and not is_force_pairing():
            set_phase("ready")
            ensure_classifier_config()
            start_fall_detection()
            log.info("Dispositivo já provisionado — a aguardar reset")
            while is_provisioned() and not cancel.is_set() and not is_force_pairing():
                await asyncio.sleep(1)
            continue

        load_or_create_identity()

        if not is_provisioned() and not is_force_pairing():
            if await ensure_mock_network():
                continue

        identity = load_or_create_identity()
        set_phase("pairing")
        reason = "re-pareamento" if is_force_pairing() else "primeiro vínculo"
        if is_ble_available():
            log.info(
                "A iniciar pareamento BLE (%s) para %s", reason, identity.device_name
            )
            await init_register_beacon(
                identity.device_id,
                identity.device_name,
                identity.mac_address,
                identity.sign_priv,
                identity.ecdh_priv,
                cancel=cancel,
            )
        else:
            log.info(
                "Pareamento BLE omitido (%s) para %s", reason, identity.device_name
            )
            await _wait_pairing_without_ble(cancel)

        if is_provisioned() and not cancel.is_set():
            clear_force_pairing()
            set_phase("ready")
            ensure_classifier_config()
            start_fall_detection()
        else:
            set_phase("idle")
