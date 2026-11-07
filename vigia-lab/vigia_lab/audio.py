"""Bipes de início/fim para quem cai (não olha a tela). Silencioso fora do Windows."""

from __future__ import annotations

import threading


def _beep(freq: int, ms: int) -> None:
    try:
        import winsound

        winsound.Beep(freq, ms)
    except Exception:
        pass


def beep(freq: int = 880, ms: int = 200) -> None:
    """Não bloqueia o laço de captura."""
    threading.Thread(target=_beep, args=(freq, ms), daemon=True).start()


def beep_start() -> None:
    beep(1200, 350)


def beep_end() -> None:
    beep(600, 600)


def beep_tick() -> None:
    beep(800, 120)
