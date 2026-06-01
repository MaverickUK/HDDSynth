import digitalio

import settings

_led = digitalio.DigitalInOut(settings.HDD_LED_PIN)
_led.direction = digitalio.Direction.OUTPUT
_led.value = False


def set_active(active):
    """Turn the external HDD activity LED on/off."""
    _led.value = bool(active)
