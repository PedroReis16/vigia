"""Menu de ecrãs no LCD 16x2."""

from __future__ import annotations

import asyncio
import enum
import logging
import time

from provision import actions
from provision import state as pairing_state
from .display import Display, fit
from .status import DeviceSnapshot, read_snapshot

log = logging.getLogger(__name__)

FLASH_SECONDS = 2.0

_STAGE_STATUS: dict[str, tuple[str, str]] = {
    pairing_state.WAITING_APP: ("VIGIA", "Aguardando app"),
    pairing_state.APP_CONNECTED: ("VIGIA", "App conectado"),
    pairing_state.USER_FOUND: ("VIGIA", "Usuario encontrado"),
    pairing_state.WAITING_WIFI: ("VIGIA", "Esperando internet"),
    pairing_state.WIFI_CONNECTING: ("WiFi", "A conectar..."),
    pairing_state.WIFI_OK: ("WiFi", "Rede OK"),
    pairing_state.WIFI_FAIL: ("WiFi", "Rede invalida"),
    pairing_state.PAIRING_ERROR: ("VIGIA", "Erro vinculo"),
}


class Screen(enum.Enum):
    CPU = 0
    WIFI = 1
    SERVICO = 2
    NOVA_REDE = 3
    UNLINK = 4


CYCLE = (Screen.CPU, Screen.WIFI, Screen.SERVICO)


class Menu:
    def __init__(self, display: Display) -> None:
        self.display = display
        self.index = 0
        self._overlay: Screen | None = None
        self.last_lines: tuple[str, str] = ("", "")
        self._flash: tuple[str, str] | None = None
        self._flash_until = 0.0
        self._dirty = True
        self._loop: asyncio.AbstractEventLoop | None = None

    def bind_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        self._loop = loop

    def _request_redraw(self) -> None:
        self.mark_dirty()
        loop = self._loop
        if loop is not None:
            loop.call_soon_threadsafe(self.refresh)

    @property
    def screen(self) -> Screen:
        if self._overlay is not None:
            return self._overlay
        return CYCLE[self.index]

    def mark_dirty(self) -> None:
        self._dirty = True

    def on_up(self) -> None:
        self._overlay = None
        self.index = (self.index - 1) % len(CYCLE)
        self._request_redraw()

    def on_down(self) -> None:
        self._overlay = None
        self.index = (self.index + 1) % len(CYCLE)
        self._request_redraw()

    def on_ok(self) -> None:
        screen = self.screen
        if screen is Screen.WIFI:
            self._overlay = Screen.NOVA_REDE
        elif screen is Screen.NOVA_REDE:
            log.info("LCD: nova rede (apagar network.json)")
            actions.clear_wifi()
            self._set_flash("WiFi", "Rede apagada")
            self._overlay = None
            self.index = CYCLE.index(Screen.CPU)
        elif screen is Screen.UNLINK:
            log.info("LCD: desvincular utilizador")
            actions.unlink_user()
            self._set_flash("VIGIA", "Desvinculado")
            self._overlay = None
            self.index = CYCLE.index(Screen.CPU)
        elif screen is Screen.SERVICO:
            log.info("LCD: restart fall-detection")
            actions.restart_fall_detection()
            self._set_flash("Servico", "A reiniciar...")
        self._request_redraw()

    def on_hold(self) -> None:
        self._overlay = Screen.UNLINK
        self._request_redraw()

    def _set_flash(self, line1: str, line2: str) -> None:
        self._flash = (line1, line2)
        self._flash_until = time.monotonic() + FLASH_SECONDS

    def lines_for(self, snap: DeviceSnapshot) -> tuple[str, str]:
        if self._flash is not None and time.monotonic() < self._flash_until:
            return self._flash
        self._flash = None

        screen = self.screen
        if screen is Screen.CPU:
            pairing = snap.phase == "pairing" or (
                not snap.provisioned and snap.phase != "ready"
            )
            if pairing:
                return _STAGE_STATUS.get(
                    snap.pairing_stage, ("VIGIA", "Aguardando app")
                )
            return f"Fall {snap.fall_cpu_pct:3d}%", f"CPU  {snap.sys_cpu_pct:3d}%"
        if screen is Screen.WIFI:
            return "WiFi", snap.ssid or "nao ligada"
        if screen is Screen.NOVA_REDE:
            return "Nova rede?", "OK confirma"
        if screen is Screen.SERVICO:
            return "Servico", "ativo" if snap.fall_active else "parado"
        return "Desvincular?", "OK confirma"

    def refresh(self, snapshot: DeviceSnapshot | None = None) -> None:
        snap = snapshot if snapshot is not None else read_snapshot()
        line1, line2 = self.lines_for(snap)
        fitted = (fit(line1), fit(line2))
        if fitted == self.last_lines and not self._dirty:
            return
        self._dirty = False
        self.last_lines = fitted
        self.display.write(line1, line2)
