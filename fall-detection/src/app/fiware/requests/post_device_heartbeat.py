from __future__ import annotations

import os

import aiohttp
from dotenv import load_dotenv

from app.fiware.requests.fiware_endpoints import orion_url


class PostDeviceHeartbeat:
    """Publica heartbeat do dispositivo no Orion."""

    def __init__(self) -> None:
        load_dotenv()
        self._orion_base_url = orion_url()
        self._fiware_service = os.getenv("FIWARE_SERVICE")

    async def execute_async(self, payload: dict) -> None:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self._orion_base_url}/v2/entities",
                headers={
                    "Content-Type": "application/json",
                    "fiware-service": self._fiware_service,
                    "fiware-servicepath": "/",
                },
                json=payload,
                timeout=30,
            ) as response:
                if response.status not in (200, 201, 204):
                    raise Exception(
                        f"Error posting heartbeat to FIWARE: {response.status} {await response.text()}"
                    )
