import json
from dataclasses import asdict
from pathlib import Path
from uuid import UUID

from app.config import Settings
from app.integration.models.vigia_settings import VigiaSettings

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

def run_integration(settings: Settings) -> None:
    _setup_fiware_device()