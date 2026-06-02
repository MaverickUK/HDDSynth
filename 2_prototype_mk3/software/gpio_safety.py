import board
import digitalio

# GP0–GP22, GP26–GP28 are the externally accessible GPIO pins on the Pico.
_EXTERNAL_GPIO_NUMBERS = list(range(0, 23)) + [26, 27, 28]

# Holds DigitalInOut refs so the GC doesn't reclaim them.
_claimed = []


def pull_down_unused(used_pins):
    """Set every unused external GPIO to INPUT with PULL_DOWN.

    Prevents floating inputs from coupling noise into the MCU core (CMOS latchup risk).
    Call before importing any module that claims GPIO pins.
    """
    used = set(used_pins)
    for n in _EXTERNAL_GPIO_NUMBERS:
        pin = getattr(board, f"GP{n}", None)
        if pin is None or pin in used:
            continue
        try:
            dio = digitalio.DigitalInOut(pin)
            dio.direction = digitalio.Direction.INPUT
            dio.pull = digitalio.Pull.DOWN
            _claimed.append(dio)
        except Exception as e:
            print(f"[gpio_safety] GP{n}: {e}")
