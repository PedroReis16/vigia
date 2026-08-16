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
    from gpiozero import Device
    from gpiozero.pins.lgpio import LGPIOFactory, LGPIOPin
    from gpiozero.pins.local import LocalPiFactory
    import lgpio

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
        self._skip_ok = False

    def fire(self, name: str, fn) -> bool:
        now = time.monotonic()
        if name == "ok" and self._skip_ok:
            self._skip_ok = False
            return False
        if now < self._until.get(name, 0.0):
            return False
        self._until[name] = now + self._lockout
        if name == "hold":
            self._skip_ok = True
            self._until["ok"] = now + 2.0
        fn()
        return True


class ButtonPoller:
    def __init__(self, btn_ok, btn_up, btn_down, hold_seconds: float, gate: _EventGate) -> None:
        self.btn_ok = btn_ok
        self.btn_up = btn_up
        self.btn_down = btn_down
        self.hold_seconds = hold_seconds
        self.gate = gate
        self._ok_since: float | None = None
        self._ok_held = False
        self._up = False
        self._down = False

    def poll(self, menu) -> None:
        up = bool(self.btn_up.is_pressed)
        if up and not self._up:
            if self.gate.fire("up", menu.on_up):
                log.info("GPIO: up")
        self._up = up

        down = bool(self.btn_down.is_pressed)
        if down and not self._down:
            if self.gate.fire("down", menu.on_down):
                log.info("GPIO: down")
        self._down = down

        pressed = bool(self.btn_ok.is_pressed)
        now = time.monotonic()
        if pressed:
            if self._ok_since is None:
                self._ok_since = now
                self._ok_held = False
            elif not self._ok_held and now - self._ok_since >= self.hold_seconds:
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
            hold_time=cfg.hold_seconds,
        )
        btn_up = Button(cfg.button_up, pull_up=True, bounce_time=bounce)
        btn_down = Button(cfg.button_down, pull_up=True, bounce_time=bounce)

        gate = _EventGate()

        def on_ok_held() -> None:
            if gate.fire("hold", menu.on_hold):
                log.info("GPIO: hold")

        def on_ok_released() -> None:
            if gate.fire("ok", menu.on_ok):
                log.info("GPIO: ok")

        def on_up() -> None:
            if gate.fire("up", menu.on_up):
                log.info("GPIO: up")

        def on_down() -> None:
            if gate.fire("down", menu.on_down):
                log.info("GPIO: down")

        btn_ok.when_held = on_ok_held
        btn_ok.when_released = on_ok_released
        btn_up.when_pressed = on_up
        btn_down.when_pressed = on_down
        _buttons = [btn_ok, btn_up, btn_down]
        _poller = ButtonPoller(btn_ok, btn_up, btn_down, cfg.hold_seconds, gate)
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
