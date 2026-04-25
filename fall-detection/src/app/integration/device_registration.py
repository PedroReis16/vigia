from __future__ import annotations

import asyncio

from app.fiware.device_sync import load_or_create_local_device_settings
from app.fiware.models.vigia_settings import VigiaSettings
from app.fiware.requests.get_fiware_device_by_id import GetFiwareDeviceById
from app.fiware.requests.post_new_vigia_device import PostNewVigiaDevice
from app.fiware.requests.post_vigia_command import PostVigiaCommand
from app.fiware.requests.put_vigia_device import PutVigiaDevice
from app.logging import get_logger

logger = get_logger("integration")


def _same_device_configuration(local: VigiaSettings, remote: VigiaSettings) -> bool:
    return local.to_dict() == remote.to_dict()


async def sync_device_registration(device_settings: VigiaSettings) -> None:
    """Sincroniza cadastro do dispositivo no FIWARE (responsabilidade da integração)."""
    remote_device = await GetFiwareDeviceById().execute_async(device_settings.device_id)
    if remote_device is None:
        await PostNewVigiaDevice().execute_async(device_settings)
        await PostVigiaCommand().execute_async(device_settings)
        logger.info("dispositivo registrado no FIWARE")
        return

    if not _same_device_configuration(device_settings, remote_device):
        await PutVigiaDevice().execute_async(device_settings)
        logger.info("dispositivo atualizado no FIWARE")
    else:
        logger.debug("dispositivo local e remoto estao sincronizados")


async def wait_for_device_registration(
    device_settings: VigiaSettings,
    retry_seconds: int = 10,
    log_prefix: str = "[integration]",
) -> None:
    while True:
        try:
            await sync_device_registration(device_settings)
            return
        except Exception as exc:
            logger.warning(
                "{} falha ao sincronizar device com FIWARE; nova tentativa em {}s. detalhe: {}",
                log_prefix,
                retry_seconds,
                exc,
            )
            await asyncio.sleep(retry_seconds)


async def bootstrap_device_registration(
    retry_seconds: int = 10,
    log_prefix: str = "[integration]",
) -> VigiaSettings:
    device_settings = load_or_create_local_device_settings()
    await wait_for_device_registration(
        device_settings=device_settings,
        retry_seconds=retry_seconds,
        log_prefix=log_prefix,
    )
    return device_settings
