from __future__ import annotations

import os
from uuid import UUID

import aiohttp
from dotenv import load_dotenv

from app.fiware.models.vigia_settings import VigiaSettings
from app.fiware.requests.fiware_endpoints import iot_agent_url
from app.logging import get_logger

logger = get_logger("fiware")


class GetFiwareDeviceById:
    def __init__(self) -> None:
        load_dotenv()
        self.iot_agent_base_url = iot_agent_url()
        self.fiware_service = os.getenv("FIWARE_SERVICE")

    async def execute_async(self, device_id: UUID) -> VigiaSettings | None:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.iot_agent_base_url}/iot/devices/{device_id}",
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                    "fiware-service": self.fiware_service,
                    "fiware-servicepath": "/",
                },
            ) as response:
                if response.status == 404:
                    return None
                if response.status != 200:
                    raise Exception(
                        f"Error fetching FIWARE device: {response.status} {await response.text()}"
                    )

                content_type = (response.headers.get("Content-Type") or "").lower()
                if "application/json" not in content_type:
                    response_text = await response.text()
                    logger.warning(
                        "lookup de device retornou resposta nao-JSON; "
                        "tratando como nao encontrado. status={}, content_type={}, "
                        "body_preview={}",
                        response.status,
                        content_type,
                        response_text[:120],
                    )
                    return None

                response_content = await response.json()
                payload = response_content.get("device", response_content)
                return VigiaSettings._from_dict(payload)
