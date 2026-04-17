import datetime
import json
from dataclasses import asdict
from pathlib import Path
from uuid import UUID
import schedule

from app.config import Settings
from app.integration.models.vigia_settings import VigiaSettings
from app.integration.requests.get_fiware_device_by_id import GetFiwareDeviceById
from app.integration.requests.post_new_vigia_device import PostNewVigiaDevice
from app.integration.requests.post_vigia_command import PostVigiaCommand

def _json_default(obj: object) -> str:
    if isinstance(obj, UUID):
        return str(obj)
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")

def _register_fiware_device(device_settings: VigiaSettings) -> None:
    try:
        tracked_device = GetFiwareDeviceById().execute(device_settings.device_id)

        if tracked_device is None:
            PostNewVigiaDevice().execute(device_settings)
            PostVigiaCommand().execute(device_settings)
        
    except Exception as e:
        print(f"Error registering FIWARE device: {e}")
        raise e

def _setup_fiware_device()-> None:
    "Configura o dispositivo, caso não exista, no FIWARE"

    # Busca o Id do dispositivo, caso não exista, cria um novo Id

    device_settings = VigiaSettings()

    device_json = Path(__file__).resolve().parents[3]/"device"/"device.json"

    try:
        if not device_json.is_file():
            device_json.parent.mkdir(parents=True, exist_ok=True)
            device_json.touch()
            payload = asdict(device_settings)
            device_json.write_text(
                json.dumps(payload, indent=4, ensure_ascii=False, default=_json_default)
            )
    except Exception as e:
        print(f"Error setting up FIWARE device: {e}")
        
        if device_json.is_file():
            device_json.unlink()
        raise e

    _register_fiware_device(device_settings)
    

def integration_task() -> None:
    print(f"Running integration task at {datetime.datetime.now()}")

def run_integration(settings: Settings) -> None:
    """
    Inicia a rotina de integração com o FIWARE
    """
    try:
        _setup_fiware_device()

        schedule.every(settings.integration_interval_seconds).seconds.do(integration_task) 

        while True:
            schedule.run_pending()

    except Exception as e:
        raise e