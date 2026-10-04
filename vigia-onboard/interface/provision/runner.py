"""Orquestra pareamento BLE e o gate da captura."""

from __future__ import annotations

import asyncio
import logging
import threading

from shared.capture_gate import hold_capture, release_capture

from .ble import ble_unavailable_reason, init_register_beacon, is_ble_available
from .classifier import ensure_classifier_config
from .identity import is_provisioned, load_or_create_identity
from .state import clear_force_pairing, is_force_pairing, set_phase
from .wifi import ensure_mock_network

log = logging.getLogger(__name__)


async def _wait_pairing_without_ble(cancel: threading.Event) -> None:
    """Mantém o supervisor vivo em debug sem stack BLE (menu/UI continuam)."""
    log.warning(
        "%s — UI/menu continuam; use identity+network.json ou active BLE no deploy",
        ble_unavailable_reason(),
    )
    while not cancel.is_set() and not is_provisioned():
        await asyncio.sleep(1)


def start_capture() -> None:
    """Abre o gate. O processo de captura, se estiver à espera, entra no loop."""
    release_capture()
    log.info("Gate da captura aberto")


async def provision_supervisor(cancel: threading.Event) -> None:
    """
    Se identity+network existem (e sem force pairing), liberta a captura.
    Caso contrário — ou após Desvincular — abre o beacon BLE.
    """
    while True:
        if cancel.is_set():
            cancel.clear()
            set_phase("idle")
            hold_capture()
            await asyncio.sleep(0.2)
            continue

        if is_provisioned() and not is_force_pairing():
            set_phase("ready")
            ensure_classifier_config()
            start_capture()
            log.info("Dispositivo já provisionado — a aguardar reset")
            while is_provisioned() and not cancel.is_set() and not is_force_pairing():
                await asyncio.sleep(1)
            continue

        hold_capture()
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
            start_capture()
        else:
            set_phase("idle")
