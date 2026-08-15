from gpiozero import Button, LED
import asyncio
import logging
import subprocess
import threading

from provision.runner import provision_supervisor

BUTTON_PIN = 17
LED_PIN = 27
LONG_PRESS_THRESHOLD = 3.0
RESET_SCRIPT = "/usr/local/bin/vigia_reset_config.sh"

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

button = Button(BUTTON_PIN, pull_up=True, bounce_time=0.05, hold_time=LONG_PRESS_THRESHOLD)
status_led = LED(LED_PIN)

pairing_cancel = threading.Event()


def on_short_press():
    log.info("Short press detectado -> exibindo status do serviço")
    result = subprocess.run(
        ["systemctl", "is-active", "fall-detection.service"],
        capture_output=True,
        text=True,
    )
    if result.stdout.strip() == "active":
        for _ in range(3):
            status_led.on()
            status_led.blink(on_time=0.15, off_time=0.15, n=1)
    else:
        status_led.on()


def on_long_press():
    log.warning("Long press detectado -> resetando configurações (reentrar em pareamento)")
    status_led.blink(on_time=0.1, off_time=0.1, n=10)
    pairing_cancel.set()
    subprocess.run([RESET_SCRIPT], check=False)
    pairing_cancel.clear()
    status_led.off()


def main():
    button.when_short_pressed = on_short_press
    button.when_long_pressed = on_long_press
    try:
        asyncio.run(provision_supervisor(pairing_cancel))
    except KeyboardInterrupt:
        log.info("Interrompido")


if __name__ == "__main__":
    main()
