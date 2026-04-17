import os

import requests
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

    def execute(self, device_settings: VigiaSettings) -> None:
        attrs = [cmd.name for cmd in device_settings.commands]
        description = os.getenv(
            "ORION_COMMAND_REGISTRATION_DESCRIPTION",
            "VigiaCam commands",
        )
        body = {
            "description": description,
            "dataProvided": {
                "entities": [
                    {
                        "id": device_settings.entity_name,
                        "type": device_settings.entity_type,
                    }
                ],
                "attrs": attrs,
            },
            "provider": {
                "http": {"url": self._provider_url},
                "legacyForwarding": True,
            },
        }

        url = f"{self._fiware_path}/orion/v2/registrations"
        response = requests.post(
            url,
            headers={
                "Content-Type": "application/json",
                "fiware-service": self._fiware_service,
                "fiware-servicepath": "/",
            },
            json=body,
            timeout=60,
        )

        if response.status_code not in (200, 201):
            raise RuntimeError(
                f"Orion registration failed: {response.status_code} {response.text}"
            )
