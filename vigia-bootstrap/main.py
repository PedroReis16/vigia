import asyncio
import logging
import signal
import threading

from provision import ota as ota_svc
from provision.identity import is_provisioned
from provision.runner import provision_supervisor
from provision.state import bind_cancel
from ui.display import create_display
from ui.gpio_setup import poll_buttons, setup_buttons
from ui.menu import Menu
from ui.pins import get_pin_config
from ui.status import read_snapshot

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

pairing_cancel = threading.Event()


POLL_SECONDS = 0.05
LCD_EVERY = 10  # 0.5 s entre writes de conteúdo lento
OTA_WATCH_EVERY = 40  # ~2 s


async def ui_loop(menu: Menu) -> None:
    tick = 0
    while True:
        poll_buttons(menu)
        menu.tick_standby()
        if tick % LCD_EVERY == 0:
            menu.refresh(read_snapshot())
        if tick % OTA_WATCH_EVERY == 0:
            _poll_ota_pending(menu)
        tick += 1
        await asyncio.sleep(POLL_SECONDS)


async def run() -> None:
    cfg = get_pin_config()
    display = create_display()
    menu = Menu(display)
    bind_cancel(pairing_cancel)
    loop = asyncio.get_running_loop()
    menu.bind_loop(loop)
    ota_svc.ensure_ota_dir()
    stopping = asyncio.Event()

    def request_stop() -> None:
        stopping.set()

    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, request_stop)
        except NotImplementedError:
            pass

    if not setup_buttons(menu, cfg):
        log.warning("Botoes desativados; provisionamento BLE continua")
    menu.refresh()
    ui = asyncio.create_task(ui_loop(menu))
    supervisor = asyncio.create_task(provision_supervisor(pairing_cancel))
    stop = asyncio.create_task(stopping.wait())
    try:
        done, pending = await asyncio.wait(
            {ui, supervisor, stop},
            return_when=asyncio.FIRST_COMPLETED,
        )
        for task in pending:
            task.cancel()
        await asyncio.gather(*pending, return_exceptions=True)
        for task in done:
            if task is stop:
                continue
            exc = task.exception() if not task.cancelled() else None
            if exc is not None:
                raise exc
    finally:
        display.close()
        log.info("LCD desligado")


def main():
    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        log.info("Interrompido")


if __name__ == "__main__":
    main()
