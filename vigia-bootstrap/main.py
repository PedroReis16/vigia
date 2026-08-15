import asyncio
import logging
import threading

from provision.runner import provision_supervisor
from ui.display import create_display
from ui.gpio_setup import setup_buttons
from ui.menu import Menu
from ui.pins import get_pin_config
from ui.status import read_snapshot

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

pairing_cancel = threading.Event()


async def ui_loop(menu: Menu) -> None:
    while True:
        menu.refresh(read_snapshot())
        await asyncio.sleep(0.5)


async def run() -> None:
    cfg = get_pin_config()
    display = create_display()
    menu = Menu(display)
    if not setup_buttons(menu, cfg):
        log.warning("Botoes desativados; provisionamento BLE continua")
    menu.refresh()
    await asyncio.gather(
        provision_supervisor(pairing_cancel),
        ui_loop(menu),
    )


def main():
    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        log.info("Interrompido")


if __name__ == "__main__":
    main()
