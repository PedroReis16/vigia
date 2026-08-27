"""Pinos GPIO e LCD (BCM), via ambiente."""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover

    def load_dotenv(*_args, **_kwargs) -> bool:
        return False


load_dotenv()


def _as_bool(value: str) -> bool:
    return value.strip().lower() in ("1", "true", "t", "yes", "y")


def _int_env(name: str, default: int, base: int = 10) -> int:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    return int(raw.strip(), base)


@dataclass(frozen=True)
class PinConfig:
    button_ok: int = 17
    button_up: int = 22
    button_down: int = 23
    lcd_i2c_addr: int = 0x27
    lcd_i2c_port: int = 1
    lcd_enabled: bool = True
    hold_seconds: float = 3.0
    lcd_standby_seconds: float = 20.0


@lru_cache(maxsize=1)
def get_pin_config() -> PinConfig:
    return PinConfig(
        button_ok=_int_env("BUTTON_OK", 17),
        button_up=_int_env("BUTTON_UP", 22),
        button_down=_int_env("BUTTON_DOWN", 23),
        lcd_i2c_addr=_int_env("LCD_I2C_ADDR", 0x27, base=0),
        lcd_i2c_port=_int_env("LCD_I2C_PORT", 1),
        lcd_enabled=_as_bool(os.getenv("LCD_ENABLED", "true")),
        hold_seconds=float(os.getenv("BUTTON_HOLD_SECONDS", "3.0")),
        lcd_standby_seconds=float(os.getenv("LCD_STANDBY_SECONDS", "20")),
    )
