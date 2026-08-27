"""Arranque GPIO (Pi 5 precisa de lgpio). Falha sem derrubar o serviço."""

from __future__ import annotations

import logging
import os
import time

from .pins import PinConfig

log = logging.getLogger(__name__)

_buttons: list = []
_poller: "ButtonPoller | None" = None


def _lgpio_chip_candidates() -> list[int]:
    chips: list[int] = []
    if os.path.exists("/dev/gpiochip4"):
        chips.append(4)
    if os.path.exists("/dev/gpiochip0"):
        chips.append(0)
    for extra in (4, 0):
        if extra not in chips:
            chips.append(extra)
    return chips


def _try_lgpio_factory() -> bool:
    """gpiozero 2.0.1 ignora o chip e força 4 no Pi 5; kernels novos usam 0."""
    try:
        from gpiozero import Device
        from gpiozero.pins.lgpio import LGPIOFactory, LGPIOPin
        from gpiozero.pins.local import LocalPiFactory
        import lgpio
    except ImportError as exc:
        # macOS / sem liblgpio: lgpio não está no requirements (marker linux).
        log.info("lgpio indisponivel (%s) — a tentar outro pin factory", exc)
        return False

    last_exc: Exception | None = None
    for chip in _lgpio_chip_candidates():
        try:
            factory = LGPIOFactory.__new__(LGPIOFactory)
            LocalPiFactory.__init__(factory)
            factory._handle = lgpio.gpiochip_open(chip)
            factory._chip = chip
            factory.pin_class = LGPIOPin
            Device.pin_factory = factory
            log.info("gpiozero: LGPIOFactory chip=%s", chip)
            return True
        except Exception as exc:
            last_exc = exc
            log.warning("LGPIOFactory chip=%s falhou: %s", chip, exc)
    if last_exc is not None:
        log.warning("LGPIOFactory indisponivel: %s", last_exc)
    return False


def configure_pin_factory() -> bool:
    """Preferir lgpio (Raspberry Pi 5). Devolve False se nenhum factory carregar."""
    from gpiozero import Device

    if _try_lgpio_factory():
        return True

    try:
        Device.ensure_pin_factory()
        log.info("gpiozero: factory por omissao %s", type(Device.pin_factory).__name__)
        return Device.pin_factory is not None
    except Exception as exc:
        log.warning("gpiozero sem pin factory: %s", exc)
        return False


class _EventGate:
    """Evita duplo disparo quando callback e poll vêem o mesmo clique."""

    def __init__(self, lockout: float = 0.2) -> None:
        self._lockout = lockout
        self._until: dict[str, float] = {}

    def fire(self, name: str, fn) -> bool:
        now = time.monotonic()
        if now < self._until.get(name, 0.0):
            return False
        self._until[name] = now + self._lockout
        fn()
        return True


class ButtonPoller:
    REPEAT_DELAY = 0.35
    REPEAT_INTERVAL = 0.07

    def __init__(self, btn_ok, btn_up, btn_down, gate: _EventGate) -> None:
        self.btn_ok = btn_ok
        self.btn_up = btn_up
        self.btn_down = btn_down
        self.gate = gate
        self._ok_since: float | None = None
        self._ok_held = False
        self._up = False
        self._down = False
        self._up_repeat_at = 0.0
        self._down_repeat_at = 0.0

    def _nav_edge_or_repeat(
        self,
        pressed: bool,
        was: bool,
        next_at: float,
        name: str,
        handler,
        menu,
        now: float,
    ) -> tuple[bool, float]:
        if pressed and not was:
            if self.gate.fire(name, handler):
                log.info("GPIO: %s", name)
            return True, now + self.REPEAT_DELAY
        if pressed and was and menu.char_repeat_enabled() and now >= next_at:
            handler()
            return True, now + self.REPEAT_INTERVAL
        if not pressed:
            return False, 0.0
        return True, next_at

    def poll(self, menu) -> None:
        up = bool(self.btn_up.is_pressed)
        down = bool(self.btn_down.is_pressed)
        pressed = bool(self.btn_ok.is_pressed)
        now = time.monotonic()

        if menu.consume_wake():
            self._up = up
            self._down = down
            self._up_repeat_at = 0.0
            self._down_repeat_at = 0.0
            if pressed:
                self._ok_since = now
                self._ok_held = True
            else:
                self._ok_since = None
                self._ok_held = False
            return

        self._up, self._up_repeat_at = self._nav_edge_or_repeat(
            up, self._up, self._up_repeat_at, "up", menu.on_up, menu, now
        )
        self._down, self._down_repeat_at = self._nav_edge_or_repeat(
            down, self._down, self._down_repeat_at, "down", menu.on_down, menu, now
        )

        hold = menu.ok_hold_seconds()
        if pressed:
            if self._ok_since is None:
                self._ok_since = now
                self._ok_held = False
            elif (
                hold is not None
                and not self._ok_held
                and now - self._ok_since >= hold
            ):
                self._ok_held = True
                if self.gate.fire("hold", menu.on_hold):
                    log.info("GPIO: hold")
        elif self._ok_since is not None:
            if not self._ok_held:
                if self.gate.fire("ok", menu.on_ok):
                    log.info("GPIO: ok")
            self._ok_since = None
            self._ok_held = False


def poll_buttons(menu) -> None:
    if _poller is not None:
        _poller.poll(menu)


def setup_buttons(menu, cfg: PinConfig) -> bool:
    """Regista os 3 botoes. Mantem referencias para nao serem GC. False se GPIO falhar."""
    global _buttons, _poller

    if not configure_pin_factory():
        return False

    from gpiozero import Button

    bounce = 0.05
    try:
        btn_ok = Button(
            cfg.button_ok,
            pull_up=True,
            bounce_time=bounce,
        )
        btn_up = Button(cfg.button_up, pull_up=True, bounce_time=bounce)
        btn_down = Button(cfg.button_down, pull_up=True, bounce_time=bounce)

        gate = _EventGate()
        _buttons = [btn_ok, btn_up, btn_down]
        _poller = ButtonPoller(btn_ok, btn_up, btn_down, gate)
    except Exception as exc:
        log.warning("GPIO indisponivel (%s) — a continuar sem botoes", exc)
        return False

    log.info(
        "GPIO: OK=%s UP=%s DOWN=%s",
        cfg.button_ok,
        cfg.button_up,
        cfg.button_down,
    )
    return True
