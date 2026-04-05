"""Job enfileirado da thread de captura para inferência pose + CSV."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class PoseProcessJob:
    """Frame já copiado; path e capture_seq definidos na thread de captura."""

    frame: Any
    csv_path: str | None
    capture_seq: int
