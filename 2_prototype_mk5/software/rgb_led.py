"""RGB status LED.

The LED (XL-3528RGBW-HM) is common anode: the shared pin is tied to +3V3 and
each colour's cathode is driven by a GPIO through its series resistor. Driving a
pin LOW therefore turns that channel ON, so the PWM duty cycle is inverted —
a level of 255 maps to a duty of 0.
"""
import time

import pwmio

import settings

_FULL_DUTY = 65535

_red = pwmio.PWMOut(settings.RGB_LED_RED_PIN,
                    frequency=settings.RGB_LED_PWM_FREQUENCY,
                    duty_cycle=_FULL_DUTY)
_green = pwmio.PWMOut(settings.RGB_LED_GREEN_PIN,
                      frequency=settings.RGB_LED_PWM_FREQUENCY,
                      duty_cycle=_FULL_DUTY)
_blue = pwmio.PWMOut(settings.RGB_LED_BLUE_PIN,
                     frequency=settings.RGB_LED_PWM_FREQUENCY,
                     duty_cycle=_FULL_DUTY)


def _duty(level):
    """Map a 0-255 brightness to an inverted 16-bit duty cycle."""
    level = min(max(int(level), 0), 255)
    return _FULL_DUTY - (level * _FULL_DUTY) // 255


def set_rgb(r, g, b):
    """Set the LED colour. Each channel is 0-255."""
    _red.duty_cycle = _duty(r)
    _green.duty_cycle = _duty(g)
    _blue.duty_cycle = _duty(b)


def off():
    set_rgb(0, 0, 0)


def parse_colour(value):
    """Parse an RGB colour from a settings value.

    Accepts [r, g, b] with each channel 0-255, or a hex string such as
    "#00FF00" or "00FF00". Returns an (r, g, b) tuple, or None if the value
    can't be understood.
    """
    if isinstance(value, str):
        text = value.strip().lstrip("#")
        if len(text) != 6:
            return None
        try:
            return (int(text[0:2], 16), int(text[2:4], 16), int(text[4:6], 16))
        except ValueError:
            return None

    if isinstance(value, (list, tuple)) and len(value) == 3:
        try:
            return tuple(min(max(int(channel), 0), 255) for channel in value)
        except (TypeError, ValueError):
            return None

    return None


# Cached so the main loop only writes to the PWM channels when the state changes.
_activity_shown = None


def set_activity(active):
    """Show HDD activity in the configured colour, if activity indication is enabled."""
    global _activity_shown

    active = bool(active) and settings.ACTIVITY_LED_ENABLED
    if active == _activity_shown:
        return
    _activity_shown = active

    if active:
        set_rgb(*settings.ACTIVITY_LED_COLOUR)
    else:
        off()


def invalidate_activity():
    """Force the next set_activity() call to rewrite the LED.

    Call after anything else has driven the LED (a beep flash, the busy
    indicator) so normal activity indication reasserts itself.
    """
    global _activity_shown
    _activity_shown = None


def flash(colour, count, on_time, gap_time=None):
    """Blocking flash pattern. Mirrors the timing of a beep profile."""
    if gap_time is None:
        gap_time = on_time * 0.4

    for index in range(count):
        set_rgb(*colour)
        time.sleep(on_time)
        off()
        if index < count - 1:
            time.sleep(gap_time)

    invalidate_activity()


# --- "Internal activity, please wait" indicator ---------------------------
# Long jobs (caching to flash, first-boot setup) block, so the flash is advanced
# by busy_tick() calls placed inside those loops rather than by a timer.

_busy_last_toggle = None
_busy_lit = False


def busy_tick():
    """Advance the busy flash. Safe to call as often as you like."""
    global _busy_last_toggle, _busy_lit

    now = time.monotonic()
    if _busy_last_toggle is not None and (now - _busy_last_toggle) < settings.RGB_LED_BUSY_FLASH_S:
        return

    _busy_last_toggle = now
    _busy_lit = not _busy_lit

    if _busy_lit:
        set_rgb(*settings.RGB_LED_BUSY_COLOUR)
    else:
        off()


def busy_end():
    """Finish the busy indication and leave the LED off."""
    global _busy_last_toggle, _busy_lit

    _busy_last_toggle = None
    _busy_lit = False
    off()
    invalidate_activity()


def hue_to_rgb(hue):
    """Map a hue (0.0-1.0) to (r, g, b) at full saturation and brightness."""
    position = (hue % 1.0) * 6.0
    sector = int(position)
    rising = int(255 * (position - sector))
    falling = 255 - rising

    if sector == 0:
        return 255, rising, 0
    if sector == 1:
        return falling, 255, 0
    if sector == 2:
        return 0, 255, rising
    if sector == 3:
        return 0, falling, 255
    if sector == 4:
        return rising, 0, 255
    return 255, 0, falling


def startup_test(duration=None, steps=None):
    """Sweep the full hue range once to confirm all three channels work."""
    if duration is None:
        duration = settings.RGB_LED_STARTUP_TEST_S
    if not duration:
        return

    if steps is None:
        steps = settings.RGB_LED_STARTUP_TEST_STEPS

    delay = duration / steps
    for step in range(steps):
        set_rgb(*hue_to_rgb(step / steps))
        time.sleep(delay)
    off()
