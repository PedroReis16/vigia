from __future__ import annotations

import os

import aiohttp
from dotenv import load_dotenv

from app.integration.requests.fiware_endpoints import orion_url


class CreateDeviceHeartbeatEntityError(Exception):
    def __init__(self, status_code: int, response_text: str) -> None:
        self.status_code = status_code
        self.response_text = response_text
        super().__init__(
            f"Error creating heartbeat entity in FIWARE: {status_code} {response_text}"
        )


class PostCreateDeviceHeartbeatEntity:
    """Cria a entidade de heartbeat no Orion (primeira execução)."""

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
                    raise CreateDeviceHeartbeatEntityError(
                        status_code=response.status,
                        response_text=await response.text(),
                    )
