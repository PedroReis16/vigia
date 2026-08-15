"""LCD 16x2 I2C (PCF8574). Sem hardware: no-op."""

from __future__ import annotations

import logging
from typing import Optional, Protocol

from .pins import get_pin_config

log = logging.getLogger(__name__)

LCD_COLS = 16
LCD_ROWS = 2


def fit(text: str, width: int = LCD_COLS) -> str:
    cleaned = (
        text.replace("ã", "a")
        .replace("á", "a")
        .replace("â", "a")
        .replace("é", "e")
        .replace("ê", "e")
        .replace("í", "i")
        .replace("ó", "o")
        .replace("ô", "o")
        .replace("õ", "o")
        .replace("ú", "u")
        .replace("ç", "c")
        .replace("Ã", "A")
        .replace("Á", "A")
        .replace("É", "E")
        .replace("Í", "I")
        .replace("Ó", "O")
        .replace("Ú", "U")
        .replace("Ç", "C")
    )
    return cleaned[:width].ljust(width)


class Display(Protocol):
    def write(self, line1: str, line2: str) -> None: ...


class NullDisplay:
    last: tuple[str, str] = ("", "")

    def write(self, line1: str, line2: str) -> None:
        self.last = (fit(line1), fit(line2))
        log.info("LCD: [%s][%s]", self.last[0].rstrip(), self.last[1].rstrip())


class I2cDisplay:
    def __init__(self) -> None:
        cfg = get_pin_config()
        from RPLCD.i2c import CharLCD

        self._lcd = CharLCD(
            i2c_expander="PCF8574",
            address=cfg.lcd_i2c_addr,
            port=cfg.lcd_i2c_port,
            cols=LCD_COLS,
            rows=LCD_ROWS,
            auto_linebreaks=False,
        )

    def write(self, line1: str, line2: str) -> None:
        self._lcd.clear()
        self._lcd.write_string(fit(line1))
        self._lcd.cursor_pos = (1, 0)
        self._lcd.write_string(fit(line2))


def create_display() -> Display:
    cfg = get_pin_config()
    if not cfg.lcd_enabled:
        log.info("LCD desativado (LCD_ENABLED=false)")
        return NullDisplay()
    try:
        return I2cDisplay()
    except Exception as exc:
        log.warning("LCD I2C indisponivel (%s) — a continuar sem display", exc)
        return NullDisplay()
