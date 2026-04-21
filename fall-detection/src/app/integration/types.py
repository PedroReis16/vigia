from __future__ import annotations

from dataclasses import dataclass
from typing import Awaitable, Callable

from app.config import Settings
from app.integration.models.vigia_settings import VigiaSettings

CommandHandler = Callable[[dict], Awaitable[None]]


@dataclass
class IntegrationContext:
    settings: Settings
    device_settings: VigiaSettings
