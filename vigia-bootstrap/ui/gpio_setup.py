"""Arranque GPIO (Pi 5 precisa de lgpio). Falha sem derrubar o serviço."""

from __future__ import annotations

import logging

from .pins import PinConfig

log = logging.getLogger(__name__)

_buttons: list = []


def configure_pin_factory() -> bool:
    """Preferir lgpio (Raspberry Pi 5). Devolve False se nenhum factory carregar."""
    from gpiozero import Device

    try:
        from gpiozero.pins.lgpio import LGPIOFactory

        Device.pin_factory = LGPIOFactory()
        log.info("gpiozero: LGPIOFactory")
        return True
    except Exception as exc:
        log.warning("LGPIOFactory indisponivel: %s", exc)

    try:
        Device.ensure_pin_factory()
        log.info("gpiozero: factory por omissao %s", type(Device.pin_factory).__name__)
        return Device.pin_factory is not None
    except Exception as exc:
        log.warning("gpiozero sem pin factory: %s", exc)
        return False


def setup_buttons(menu, cfg: PinConfig) -> bool:
    """Regista os 3 botoes. Mantem referencias para nao serem GC. False se GPIO falhar."""
    global _buttons

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

        # gpiozero 2.0 não tem when_short_pressed / when_long_pressed.
        ok_held = {"v": False}

        def on_ok_held() -> None:
            ok_held["v"] = True
            menu.on_hold()

        def on_ok_released() -> None:
            if ok_held["v"]:
                ok_held["v"] = False
                return
            menu.on_ok()

        btn_ok.when_held = on_ok_held
        btn_ok.when_released = on_ok_released
        btn_up.when_pressed = menu.on_up
        btn_down.when_pressed = menu.on_down
        _buttons = [btn_ok, btn_up, btn_down]
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
