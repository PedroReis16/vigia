import os

import aiohttp
from dotenv import load_dotenv

from app.integration.models.vigia_settings import VigiaSettings


class PostVigiaCommand:
    """
    Context Source Registration no Orion: encaminha comandos/atributos monitorados
    para o IoT Agent (`provider.http.url`, `legacyForwarding`).
    """

    def __init__(self) -> None:
        load_dotenv()
        self._fiware_path = (os.getenv("FIWARE_PATH") or "").rstrip("/")
        self._fiware_service = os.getenv("FIWARE_SERVICE")
        self._provider_url = (
            os.getenv("ORION_COMMAND_PROVIDER_URL") or f"{self._fiware_path}/iot-agent"
        ).rstrip("/")

    async def execute_async(self, device_settings: VigiaSettings) -> None:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self._fiware_path}/orion/v2/registrations",
                headers={
                    "Content-Type": "application/json",
                    "fiware-service": self._fiware_service,
                    "fiware-servicepath": "/",
                },
                json=device_settings.to_json(),
                timeout=60,
            ) as response:
                if response.status != 200:
                    raise Exception(f"Error posting command to FIWARE: {response.status} {await response.text()}")