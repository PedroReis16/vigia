from gpiozero import Button, LED
from signal import pause
import subprocess
import logging

BUTTON_PIN = 17
LED_PIN = 27
LONG_PRESS_THRESHOLD = 3.0

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

button = Button(BUTTON_PIN, pull_up=True, bounce_time=0.05, hold_time=LONG_PRESS_THRESHOLD)
status_led = LED(LED_PIN)

def on_short_press():
    log.info("Short press detectado -> exibindo status do serviço")
    result = subprocess.run(
        ["systemctl", "is-active", "fall-detection.service"],
        capture_output=True, text=True
    )
    if result.stdout.strip() == "active":
        # pisca rápido = tudo ok
        for _ in range(3):
            status_led.on(); status_led.blink(on_time=0.15, off_time=0.15, n=1)
    else:
        # LED aceso fixo = serviço fora do ar
        status_led.on()

def on_long_press():
    log.warning("Long press detectado -> resetando configurações de usuário")
    status_led.blink(on_time=0.1, off_time=0.1, n=10)  # feedback visual imediato
    subprocess.run(["/usr/local/bin/vigia_reset_config.sh"], check=False)
    status_led.off()


def main():
    button.when_short_pressed = on_short_press
    button.when_long_pressed = on_long_press
    pause()


if __name__ == "__main__":
    main()