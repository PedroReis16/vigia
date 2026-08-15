"""Serviço de conexão Wi‑Fi (NetworkManager em release, mock em testes)."""

from __future__ import annotations

import abc
import asyncio
import json
import logging
from typing import Optional

from .settings import get_network_path, get_settings

logger = logging.getLogger(__name__)


class WifiService(abc.ABC):
    @abc.abstractmethod
    async def connect(self, ssid: str, password: str) -> None:
        """Conecta à rede Wi‑Fi. Levanta exceção em caso de falha."""


async def _nmcli(*args: str) -> tuple[int, str]:
    proc = await asyncio.create_subprocess_exec(
        "nmcli",
        *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()
    out = (stdout or b"").decode("utf-8", errors="replace").strip()
    err = (stderr or b"").decode("utf-8", errors="replace").strip()
    code = proc.returncode or 0
    if code != 0:
        return code, err or out
    return code, out or err


def _parse_active_ssid(nmcli_wifi_list: str) -> str | None:
    for line in nmcli_wifi_list.splitlines():
        parts = line.split(":", 1)
        if len(parts) == 2 and parts[0] == "yes" and parts[1].strip():
            return parts[1].strip()
    return None


def _wireless_names_for_ssid(nmcli_con_show: str, ssid: str) -> list[str]:
    names: list[str] = []
    for line in nmcli_con_show.splitlines():
        parts = line.split(":")
        if len(parts) < 2:
            continue
        name, kind = parts[0], parts[1]
        if kind != "802-11-wireless":
            continue
        if name == ssid or name.startswith(f"{ssid} "):
            names.append(name)
    return names


class NmcliWifiService(WifiService):
    async def _active_ssid(self) -> str | None:
        code, out = await _nmcli("-t", "-f", "ACTIVE,SSID", "device", "wifi")
        if code != 0:
            return None
        return _parse_active_ssid(out)

    async def _delete_stale_profiles(self, ssid: str) -> None:
        code, out = await _nmcli("-t", "-f", "NAME,TYPE", "connection", "show")
        if code != 0:
            return
        for name in _wireless_names_for_ssid(out, ssid):
            del_code, del_out = await _nmcli("connection", "delete", name)
            logger.info(
                "nmcli: apagar perfil %r (code=%s) %s", name, del_code, del_out
            )

    async def _associated(self, ssid: str) -> bool:
        active = await self._active_ssid()
        return active == ssid

    async def connect(self, ssid: str, password: str) -> None:
        if await self._associated(ssid):
            logger.info("Wi‑Fi já associado a ssid=%r — a reutilizar", ssid)
            return

        await self._delete_stale_profiles(ssid)
        await _nmcli("device", "wifi", "rescan")
        await asyncio.sleep(1.5)

        cmd = [
            "--wait",
            "30",
            "device",
            "wifi",
            "connect",
            ssid,
            "password",
            password,
        ]
        code, detail = await _nmcli(*cmd)
        if code != 0:
            # Perfil da 1.ª ligação ainda ativo, ou nome duplicado.
            if await self._associated(ssid):
                logger.info(
                    "nmcli connect falhou mas já estamos em %r: %s", ssid, detail
                )
                return
            await self._delete_stale_profiles(ssid)
            code, detail = await _nmcli(*cmd)
            if code != 0:
                if await self._associated(ssid):
                    return
                raise RuntimeError(
                    f"nmcli falhou (code={code}): {detail or 'sem detalhe'}"
                )

        if not await self._associated(ssid):
            # NM por vezes tarda a marcar ACTIVE=yes.
            await asyncio.sleep(2)
            if not await self._associated(ssid):
                raise RuntimeError(
                    f"Wi‑Fi não ficou associado a ssid={ssid!r} após nmcli"
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


def persist_network_credentials(
    ssid: str, password: str, api_base_url: str, fiware_api_key: str
) -> None:
    network_path = get_network_path()
    network_path.parent.mkdir(parents=True, exist_ok=True)
    network_path.write_text(
        json.dumps(
            {
                "ssid": ssid,
                "password": password,
                "api_base_url": api_base_url,
                "fiware_api_key": fiware_api_key,
            }
        )
    )
    network_path.chmod(0o600)


def discard_network_credentials() -> None:
    path = get_network_path()
    if path.exists():
        path.unlink()


async def connect_and_persist(
    ssid: str,
    password: str,
    api_base_url: str,
    fiware_api_key: str,
    service: WifiService | None = None,
) -> None:
    """Liga à rede e só então grava network.json. Em falha não deixa ficheiro."""
    wifi = service or get_wifi_service()
    try:
        await wifi.connect(ssid, password)
    except Exception:
        discard_network_credentials()
        raise
    persist_network_credentials(ssid, password, api_base_url, fiware_api_key)


def get_wifi_service() -> WifiService:
    settings = get_settings()
    if settings.wifi_mock:
        return MockWifiService(result=settings.wifi_mock_result)
    return NmcliWifiService()
