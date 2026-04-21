from __future__ import annotations

import os

import aiohttp
from dotenv import load_dotenv

from app.integration.requests.fiware_endpoints import orion_url


class GetOrionEntityById:
    def __init__(self) -> None:
        load_dotenv()
        self._orion_base_url = orion_url()
        self._fiware_service = os.getenv("FIWARE_SERVICE")

    async def execute_async(self, entity_id: str) -> dict | None:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self._orion_base_url}/v2/entities/{entity_id}",
                headers={
                    "Accept": "application/json",
                    "fiware-service": self._fiware_service,
                    "fiware-servicepath": "/",
                },
                timeout=30,
            ) as response:
                if response.status == 404:
                    return None
                if response.status != 200:
                    raise Exception(
                        f"Error fetching Orion entity: {response.status} {await response.text()}"
                    )
                return await response.json()
