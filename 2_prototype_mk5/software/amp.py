import digitalio

import settings

# Initialize SDMODE pin for amplifier power control if enabled
_sdmode = None
if settings.AMP_POWER_CONTROL:
    _sdmode = digitalio.DigitalInOut(settings.AMP_SDMODE_PIN)
    _sdmode.direction = digitalio.Direction.OUTPUT
    _sdmode.value = False  # Start with amp off


def power_on():
    """Turn the MAX98357A amplifier on via SDMODE pin."""
    if _sdmode is not None:
        print("[amp] Turning amplifier ON")
        _sdmode.value = True


def power_off():
    """Turn the MAX98357A amplifier off via SDMODE pin."""
    if _sdmode is not None:
        print("[amp] Turning amplifier OFF")
        _sdmode.value = False
