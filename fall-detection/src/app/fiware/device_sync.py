from __future__ import annotations

from app.config.data_workspace import device_settings_path_from_env
from app.fiware.models.vigia_settings import VigiaSettings
from app.fiware.requests.get_fiware_device_by_id import GetFiwareDeviceById


def _device_json_path():
    return device_settings_path_from_env()


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


def load_local_device_settings_required() -> VigiaSettings:
    device_json = _device_json_path()
    if not device_json.exists():
        raise RuntimeError(
            "[fiware] dispositivo nao registrado localmente. "
            "Execute o modulo de integracao primeiro para criar "
            "DATA_PATH/device/device.json."
        )

    content = device_json.read_text(encoding="utf-8").strip()
    if not content:
        raise RuntimeError(
            "[fiware] arquivo DATA_PATH/device/device.json vazio. "
            "Execute o modulo de integracao novamente para registrar o dispositivo."
        )

    return VigiaSettings.from_json(content)


async def ensure_fiware_device_registered(device_settings: VigiaSettings) -> None:
    remote_device = await GetFiwareDeviceById().execute_async(device_settings.device_id)
    if remote_device is None:
        raise RuntimeError(
            "[fiware] dispositivo nao encontrado no FIWARE. "
            "Execute o modulo de integracao para concluir o registro inicial."
        )
