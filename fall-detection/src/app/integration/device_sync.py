from __future__ import annotations

from pathlib import Path

from app.integration.models.vigia_settings import VigiaSettings
from app.integration.requests.get_fiware_device_by_id import GetFiwareDeviceById
from app.integration.requests.post_new_vigia_device import PostNewVigiaDevice
from app.integration.requests.post_vigia_command import PostVigiaCommand
from app.integration.requests.put_vigia_device import PutVigiaDevice


def _device_json_path() -> Path:
    return Path(__file__).resolve().parents[3] / "device" / "device.json"


def load_or_create_local_device_settings() -> VigiaSettings:
    device_json = _device_json_path()
    if not device_json.exists():
        device_json.parent.mkdir(parents=True, exist_ok=True)
        device_settings = VigiaSettings()
        device_json.write_text(device_settings.to_json(), encoding="utf-8")
        return device_settings

    content = device_json.read_text(encoding="utf-8").strip()
    if not content:
        device_settings = VigiaSettings()
        device_json.write_text(device_settings.to_json(), encoding="utf-8")
        return device_settings

    return VigiaSettings.from_json(content)


def _same_device_configuration(local: VigiaSettings, remote: VigiaSettings) -> bool:
    return local.to_dict() == remote.to_dict()


async def ensure_fiware_device_synced(device_settings: VigiaSettings) -> None:
    remote_device = await GetFiwareDeviceById().execute_async(device_settings.device_id)
    if remote_device is None:
        await PostNewVigiaDevice().execute_async(device_settings)
        await PostVigiaCommand().execute_async(device_settings)
        print("[integration] dispositivo registrado no FIWARE")
        return

    if not _same_device_configuration(device_settings, remote_device):
        await PutVigiaDevice().execute_async(device_settings)
        print("[integration] dispositivo atualizado no FIWARE")
    else:
        print("[integration] dispositivo local e remoto estao sincronizados")
