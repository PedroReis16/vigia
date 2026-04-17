from __future__ import annotations

import os
from uuid import UUID
from dotenv import load_dotenv
import requests

from app.integration.models.vigia_settings import VigiaSettings


class GetFiwareDeviceById:
    """
    Busca o dispositivo no FIWARE
    """

    def __init__(self):
        load_dotenv()
        self.fiware_path = os.getenv("FIWARE_PATH")
        self.fiware_service = os.getenv("FIWARE_SERVICE")

    def execute(self, device_id: UUID) -> VigiaSettings | None:
        """
        Busca o dispositivo no FIWARE
        """

        request = requests.get(
            f"{self.fiware_path}/iot-agent/iot/devices/{device_id}",
            headers={
                "Content-Type": "application/json", 
                "fiware-service": self.fiware_service,
                "fiware-servicepath": "/"
            }
        )

        if request.status_code != 200:
            return None

        return VigiaSettings.model_validate_json(request.json())
