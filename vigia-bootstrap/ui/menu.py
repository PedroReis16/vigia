"""Menu de ecrãs no LCD 16x2."""

from __future__ import annotations

import enum
import logging
import time

from provision import actions
from .display import Display, fit
from .status import DeviceSnapshot, read_snapshot

log = logging.getLogger(__name__)

PAIRING_SNAPBACK_SECONDS = 2.0


class Screen(enum.Enum):
    STATUS = 0
    WIFI = 1
    NOVA_REDE = 2
    SERVICO = 3
    UNLINK = 4


SCREENS = (
    Screen.STATUS,
    Screen.WIFI,
    Screen.NOVA_REDE,
    Screen.SERVICO,
    Screen.UNLINK,
)


class Menu:
    def __init__(self, display: Display) -> None:
        self.display = display
        self.index = 0
        self._last_nav = 0.0
        self.last_lines: tuple[str, str] = ("", "")

    @property
    def screen(self) -> Screen:
        return SCREENS[self.index]

    def on_up(self) -> None:
        self.index = (self.index - 1) % len(SCREENS)
        self._last_nav = time.monotonic()
        self.refresh()

    def on_down(self) -> None:
        self.index = (self.index + 1) % len(SCREENS)
        self._last_nav = time.monotonic()
        self.refresh()

    def on_ok(self) -> None:
        snap = read_snapshot()
        screen = self.screen
        if screen is Screen.WIFI:
            self.index = SCREENS.index(Screen.NOVA_REDE)
        elif screen is Screen.NOVA_REDE:
            log.info("LCD: nova rede (apagar network.json)")
            actions.clear_wifi()
            self.index = SCREENS.index(Screen.STATUS)
        elif screen is Screen.UNLINK:
            log.info("LCD: desvincular utilizador")
            actions.unlink_user()
            self.index = SCREENS.index(Screen.STATUS)
        elif screen is Screen.SERVICO:
            log.info("LCD: restart fall-detection")
            actions.restart_fall_detection()
        self._last_nav = time.monotonic()
        self.refresh()

    def on_hold(self) -> None:
        self.index = SCREENS.index(Screen.UNLINK)
        self._last_nav = time.monotonic()
        self.refresh()

    def lines_for(self, snap: DeviceSnapshot) -> tuple[str, str]:
        screen = self.screen
        if screen is Screen.STATUS:
            if snap.phase == "pairing" or (
                not snap.provisioned and snap.phase != "ready"
            ):
                line2 = "Pareando user"
            elif snap.fall_active:
                line2 = "Fall ativo"
            elif snap.provisioned:
                line2 = "Fall parado"
            else:
                line2 = "Sem rede"
            return "VIGIA", line2
        if screen is Screen.WIFI:
            return "WiFi", snap.ssid or "nao ligada"
        if screen is Screen.NOVA_REDE:
            return "Nova rede?", "OK confirma"
        if screen is Screen.SERVICO:
            return "Servico", "ativo" if snap.fall_active else "parado"
        return "Desvincular?", "OK confirma"

    def refresh(self, snapshot: DeviceSnapshot | None = None) -> None:
        snap = snapshot if snapshot is not None else read_snapshot()
        pairing = snap.phase == "pairing"
        if pairing and (time.monotonic() - self._last_nav) >= PAIRING_SNAPBACK_SECONDS:
            self.index = SCREENS.index(Screen.STATUS)
        line1, line2 = self.lines_for(snap)
        self.last_lines = (fit(line1), fit(line2))
        self.display.write(line1, line2)
