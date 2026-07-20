import time
import random
import digitalio

import settings

# --- Simulated access state ---
_next_switch_time = 0
_current_access_state = False

# --- Physical access input ---
# Optocoupler output is pulled LOW when the HDD activity line is active.
_phys_input = digitalio.DigitalInOut(settings.ACTIVITY_INPUT_PIN)
_phys_input.direction = digitalio.Direction.INPUT
_phys_input.pull = digitalio.Pull.UP

_last_active_time = 0


def _detect_physical_access():
    """Sensitive physical access detection.
    Triggers instantly on a LOW signal and holds 'True' for ACCESS_HOLD_TIME_MS after.
    """
    global _last_active_time

    now = time.monotonic()
    currently_active = not _phys_input.value

    if currently_active:
        # Fast attack: record the exact moment we saw activity
        _last_active_time = now
        return True

    # Slow release: stay 'True' if we saw activity within the last X milliseconds
    return (now - _last_active_time) < (settings.ACCESS_HOLD_TIME_MS / 1000.0)


def _get_simulated_access():
    global _next_switch_time, _current_access_state

    now = time.monotonic()
    if now >= _next_switch_time:
        _current_access_state = random.choice([True, False])
        _next_switch_time = now + random.uniform(0, 2)

    return _current_access_state


def get_access():
    """Return current access state: simulated or physical depending on settings."""
    if settings.SIMULATION_MODE:
        return _get_simulated_access()
    return _detect_physical_access()
