"""Serviço de conexão Wi‑Fi (NetworkManager em release, mock em debug)."""

from __future__ import annotations

import abc
import asyncio
import logging
from typing import Optional

from .settings import get_settings

logger = logging.getLogger(__name__)


class WifiService(abc.ABC):
    @abc.abstractmethod
    async def connect(self, ssid: str, password: str) -> None:
        """Conecta à rede Wi‑Fi. Levanta exceção em caso de falha."""


class NmcliWifiService(WifiService):
    async def connect(self, ssid: str, password: str) -> None:
        cmd = [
            "nmcli",
            "--wait",
            "30",
            "device",
            "wifi",
            "connect",
            ssid,
            "password",
            password,
        ]
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        if proc.returncode != 0:
            detail = (stderr or stdout or b"").decode("utf-8", errors="replace").strip()
            raise RuntimeError(
                f"nmcli falhou (code={proc.returncode}): {detail or 'sem detalhe'}"
            )

        check = await asyncio.create_subprocess_exec(
            "nmcli",
            "networking",
            "connectivity",
            "check",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        check_out, check_err = await check.communicate()
        status = (
            (check_out or check_err or b"")
            .decode("utf-8", errors="replace")
            .strip()
            .lower()
        )
        if check.returncode != 0 or status in ("none", "unknown", ""):
            raise RuntimeError(
                f"Wi‑Fi sem conectividade após nmcli: {status or 'falha'}"
            )


class MockWifiService(WifiService):
    def __init__(
        self, result: Optional[str] = None, delay_seconds: float = 0.5
    ) -> None:
        self._result = (
            (result or get_settings().wifi_mock_result or "success").strip().lower()
        )
        self._delay_seconds = delay_seconds

    async def connect(self, ssid: str, password: str) -> None:
        logger.info(
            "MockWifiService: conectando a ssid=%r (result=%s)", ssid, self._result
        )
        await asyncio.sleep(self._delay_seconds)
        if self._result == "fail":
            raise RuntimeError(f"Mock Wi‑Fi falhou para ssid={ssid!r}")


def get_wifi_service() -> WifiService:
    settings = get_settings()
    if settings.debug:
        return MockWifiService(result=settings.wifi_mock_result)
    return NmcliWifiService()
