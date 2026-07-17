import asyncio
from typing import Any, Optional
from bless import BlessServer
from bless.backends.attribute import GATTAttributePermissions
from bless.backends.characteristic import (
    BlessGATTCharacteristic,
    GATTCharacteristicProperties,
)


SERVICE_UID = "87fa2616-1953-4d5a-80d6-40201b9347eb"
SERVICE_NAME = "Vigia"
WRITE_CHAR_UUID = "14159635-68c6-4738-a066-9021e60d1efe"
NOTIFY_CHAR_UUID = "24159635-68c6-4738-a066-9021e60d1eff"

server: BlessServer = None
loop: Optional[asyncio.AbstractEventLoop] = None


async def send_response(texto: str):
    """
    Envia dado do servidor -> cliente via notify.
    Precisa que a characteristic tenha a flag 'notify' ou 'indicate'.
    """
    char = server.get_characteristic(NOTIFY_CHAR_UUID)
    char.value = texto.encode("utf-8")
    server.update_value(SERVICE_UID, NOTIFY_CHAR_UUID)


def receive_command(command: str):
    print(f"Comando recebido: {command}")


def read_request(characteristic: BlessGATTCharacteristic, **kwargs) -> bytearray:
    print(f"Lendo {characteristic.value}")
    return characteristic.value


def write_request(characteristic: BlessGATTCharacteristic, value: Any, **kwargs):
    """
    Chamado toda vez que o cliente escreve na characteristic.
    'value' é o bytearray recebido.
    """
    characteristic.value = value
    comando = value.decode("utf-8", errors="ignore")

    # write_request roda numa thread do CoreBluetooth, fora do event loop.
    # Agenda o processamento de volta no loop principal de forma thread-safe.
    if loop is not None and loop.is_running():
        loop.call_soon_threadsafe(receive_command, comando)
    else:
        receive_command(comando)


async def init_register_beacon():
    """
    Esse método será responsável por iniciar o beacon para registro do dispositivo embarcado com as informações do usuário
    """

    global server, loop
    loop = asyncio.get_running_loop()
    server = BlessServer(SERVICE_NAME, loop=loop)
    server.read_request_func = read_request
    server.write_request_func = write_request

    # Add Service
    await server.add_new_service(SERVICE_UID)

   # Characteristic de comando (cliente -> servidor)
    await server.add_new_characteristic(
        SERVICE_UID,
        WRITE_CHAR_UUID,
        GATTCharacteristicProperties.write | GATTCharacteristicProperties.write_without_response,
        None,
        GATTAttributePermissions.writeable,
    )

    # Characteristic de resposta/evento (servidor -> cliente)
    await server.add_new_characteristic(
        SERVICE_UID,
        NOTIFY_CHAR_UUID,
        GATTCharacteristicProperties.read | GATTCharacteristicProperties.notify,
        None,
        GATTAttributePermissions.readable,
    )

    # Start advertising and handling requests
    await server.start()
    print("Beacon de registro do dispositivo embarcado com bluetooth iniciado...")

    # Keep the server alive
    try:
        while True:
            await asyncio.sleep(1)
    except asyncio.CancelledError:
        pass
    finally:
        await server.stop()
