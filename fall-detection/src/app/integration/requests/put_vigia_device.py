from __future__ import annotations

import os

import aiohttp
from dotenv import load_dotenv

from app.integration.models.vigia_settings import VigiaSettings
from app.integration.requests.fiware_endpoints import iot_agent_url


class PutVigiaDevice:
    """Atualiza configuração de um dispositivo existente no IoT Agent."""

    def __init__(self) -> None:
        load_dotenv()
        self.iot_agent_base_url = iot_agent_url()
        self.fiware_service = os.getenv("FIWARE_SERVICE")

    async def execute_async(self, device_settings: VigiaSettings) -> None:
        body = {"devices": [device_settings.to_dict()]}

        async with aiohttp.ClientSession() as session:
            async with session.put(
                f"{self.iot_agent_base_url}/iot/devices/{device_settings.device_id}",
                headers={
                    "Content-Type": "application/json",
                    "fiware-service": self.fiware_service,
                    "fiware-servicepath": "/",
                },
                json=body,
            ) as response:
                if response.status not in (200, 204):
                    raise Exception(
                        f"Error updating device in FIWARE: {response.status} {await response.text()}"
                    )
