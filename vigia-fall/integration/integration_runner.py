"""
Módulo de runner para a integração do dispositivo com o serviço externo
"""

import asyncio
from uuid import UUID

from shared import helpers_create_device_name, helpers_get_mac_address
from database import create_database, get_device, create_device

is_connected: bool = False


def __register_device() -> tuple[UUID, str]:
    """
    Registro das informações iniciais do dispositivo
    """

    device_name = helpers_create_device_name()
    mac_address = helpers_get_mac_address()

    tracked_device = get_device()

    if tracked_device:
        return tracked_device.id, tracked_device.name

    device = create_device(device_name, mac_address)

    return device.id, device.name


async def initialize_device() -> None:
    """
    Inicialização dos dados de integração do dispositivo.
    O processo de inicialização somente é concluído após o dispositivo ter sido vinculado a um usuário
    """

    global is_connected
    is_connected = False

    create_database()

    device_id, device_name = __register_device()

    print(f"Device ID: {device_id}")
    print(f"Device Name: {device_name}")

    # await init_register_beacon(device_id, device_name)

    # while not is_connected:
    #     await asyncio.sleep(1)

    # print("Device connected")
