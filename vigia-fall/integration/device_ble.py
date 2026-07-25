import asyncio
from typing import Optional
from uuid import UUID
from bless import BlessServer

server: BlessServer = None
loop: Optional[asyncio.AbstractEventLoop] = None

async def init_register_beacon(device_id: UUID, device_name: str) -> None:
    """
    Inicialização do beacon do dispositivo para conexão via Bluetooth
    """
    global server, loop
    loop = asyncio.get_event_loop()
    server = BlessServer(device_name, loop=loop)

    await server.add_new_service(device_id)




    await server.start()

    seconds = 0

    while seconds < 60:
        await asyncio.sleep(1)
        seconds += 1

    

    