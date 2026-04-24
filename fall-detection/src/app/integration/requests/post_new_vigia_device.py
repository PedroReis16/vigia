import os
from dotenv import load_dotenv
import aiohttp

from app.integration.models.vigia_settings import VigiaSettings
from app.integration.requests.fiware_endpoints import iot_agent_url

class PostNewVigiaDevice:

    def __init__(self):
        load_dotenv()
        self.iot_agent_base_url = iot_agent_url()
        self.fiware_service = os.getenv("FIWARE_SERVICE")

    async def execute_async(self, device_settings: VigiaSettings) -> None:
        """
        Cria um novo dispositivo no FIWARE
        """

        # IoT Agent exige `{"devices": [ ... ]}`, não o objeto do dispositivo na raiz.
        body = {"devices": [device_settings.to_dict()]}

        async with aiohttp.ClientSession() as session:
            async with session.post(
            f"{self.iot_agent_base_url}/iot/devices",
            headers={
                "Content-Type": "application/json",
                "fiware-service": self.fiware_service,
                "fiware-servicepath": "/",
            },
                json=body,
            ) as response:
                if response.status != 201:
                    raise Exception(f"Error creating new device in FIWARE: {response.status} {await response.text()}")


