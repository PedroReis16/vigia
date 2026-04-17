import os
from dotenv import load_dotenv
import requests

from app.integration.models.vigia_settings import VigiaSettings

class PostNewVigiaDevice:

    def __init__(self):
        load_dotenv()
        self.fiware_path = os.getenv("FIWARE_PATH")
        self.fiware_service = os.getenv("FIWARE_SERVICE")

    def execute(self, device_settings: VigiaSettings) -> None:
        """
        Cria um novo dispositivo no FIWARE
        """

        # IoT Agent exige `{"devices": [ ... ]}`, não o objeto do dispositivo na raiz.
        body = {"devices": [device_settings.to_dict()]}

        request = requests.post(
            f"{self.fiware_path}/iot-agent/iot/devices",
            headers={
                "Content-Type": "application/json",
                "fiware-service": self.fiware_service,
                "fiware-servicepath": "/",
            },
            json=body,
        )

        if request.status_code != 201:
            raise Exception(f"Error creating new device in FIWARE: {request.status_code} {request.text}")


