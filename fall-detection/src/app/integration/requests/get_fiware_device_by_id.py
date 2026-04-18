from __future__ import annotations

import os
from uuid import UUID
from dotenv import load_dotenv
import aiohttp

from app.integration.models.vigia_settings import VigiaSettings


class GetFiwareDeviceById:
    """
    Busca o dispositivo no FIWARE
    """

    def __init__(self):
        load_dotenv()
        self.fiware_path = os.getenv("FIWARE_PATH")
        self.fiware_service = os.getenv("FIWARE_SERVICE")

    async def execute_async(self, device_id: UUID) -> VigiaSettings | None:
        """
        Busca o dispositivo no FIWARE
        """
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.fiware_path}/iot-agent/iot/devices/{device_id}",
                headers={
                    "Content-Type": "application/json", 
                    "fiware-service": self.fiware_service,
                    "fiware-servicepath": "/"
                }
            ) as response:
                if response.status != 200:
                    return None
                
                response_content = await response.json()
                return VigiaSettings.from_json(response_content)