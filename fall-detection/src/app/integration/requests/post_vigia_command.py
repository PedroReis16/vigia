import os

import aiohttp
from dotenv import load_dotenv

from app.integration.models.vigia_settings import VigiaSettings
from app.integration.requests.fiware_endpoints import iot_agent_url, orion_url


class PostVigiaCommand:
    """
    Context Source Registration no Orion: encaminha comandos/atributos monitorados
    para o IoT Agent (`provider.http.url`, `legacyForwarding`).
    """

    def __init__(self) -> None:
        load_dotenv()
        self._orion_base_url = orion_url()
        self._iot_agent_base_url = iot_agent_url()
        self._fiware_service = os.getenv("FIWARE_SERVICE")
        self._provider_url = (
            os.getenv("ORION_COMMAND_PROVIDER_URL") or self._iot_agent_base_url
        ).rstrip("/")

    async def execute_async(self, device_settings: VigiaSettings) -> None:
        registration_payload = {
            "description": f"Vigia commands registration for {device_settings.entity_name}",
            "dataProvided": {
                "entities": [
                    {
                        "id": device_settings.entity_name,
                        "type": device_settings.entity_type,
                    }
                ],
                "attrs": [command.name for command in device_settings.commands],
            },
            "provider": {
                "http": {
                    "url": self._provider_url,
                },
                "legacyForwarding": True,
            },
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self._orion_base_url}/v2/registrations",
                headers={
                    "Content-Type": "application/json",
                    "fiware-service": self._fiware_service,
                    "fiware-servicepath": "/",
                },
                json=registration_payload,
                timeout=60,
            ) as response:
                if response.status not in (200, 201, 204):
                    raise Exception(f"Error posting command to FIWARE: {response.status} {await response.text()}")