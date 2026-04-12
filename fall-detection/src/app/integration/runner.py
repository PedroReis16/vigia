import json
from pathlib import Path
import uuid
from app.config import Settings
import os
from app.integration.models.vigia_settings import VigiaSettings

def _setup_fiware_device()-> None:
    "Configura o dispositivo, caso não exista, no FIWARE"

    # Busca o Id do dispositivo, caso não exista, cria um novo Id

    device_settings = VigiaSettings()

    device_json = Path(__file__).resolve().parents[3]/"device"/"device.json"

    if device_json.is_file():
        print(f"Device JSON found: {device_json}")
    else:
        print(f"Device JSON not found: {device_json}")
        print(json.dumps(device_settings, indent=4))
    

def run_integration(settings: Settings) -> None:
    _setup_fiware_device()