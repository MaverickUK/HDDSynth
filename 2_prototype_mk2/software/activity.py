import time
import random
import digitalio
import board

import settings

# Initial setup for simulated mode
next_switch_time = 0
current_access_state = False

# Physical input object (initialized lazily)
_phys_input = None


def _init_physical_input():
    """Lazily initialize the `DigitalInOut` used to read physical HDD activity.

    The optocoupler output is wired to `board.GP16`. The opto emitter is
    tied to ground so we enable the internal pull-up and treat a LOW
    reading as "activity" (the opto transistor conducts to ground).
    """
    global _phys_input
    if _phys_input is not None:
        return
    try:
        d = digitalio.DigitalInOut(board.GP26)
        d.direction = digitalio.Direction.INPUT
        # Pull-up is the safest default given the opto emitter is grounded
        try:
            d.pull = digitalio.Pull.UP
        except Exception:
            # Some builds may not expose Pull; ignore if unsupported
            pass
        _phys_input = d
    except Exception:
        _phys_input = None




# Updated, more sensitive
_last_active_time = 0

def _detect_physical_access(hold_time_ms=50):
    """
    Sensitive physical access detection.
    Triggers INSTANTLY on a LOW signal and holds 'True' for hold_time_ms.
    """
    global _last_active_time

    _init_physical_input()
    if _phys_input is None:
        return False

    now = time.monotonic()
    try:
        # Read the pin - LOW (False) is activity
        currently_active = not _phys_input.value
    except Exception:
        return False

    if currently_active:
        # Fast Attack: Record the exact moment we saw activity
        _last_active_time = now
        return True
    
    # Slow Release: Stay 'True' if we saw activity within the last X milliseconds
    if (now - _last_active_time) < (hold_time_ms / 1000.0):
        return True

    return False

# Stateful debounce variables for non-blocking detection
# _last_phys_state = None
# _last_phys_change_time = 0
# _last_stable_active = False


# def _detect_physical_access(debounce_ms=10):
#     """Non-blocking physical access detection.

#     Reads the GP16 input once per call and uses a simple stateful
#     debounce so the function never sleeps or blocks the caller.
#     Returns True when the input has been observed LOW (optocoupler
#     conducting) and stable for at least `debounce_ms` milliseconds.
#     """
#     global _last_phys_state, _last_phys_change_time, _last_stable_active

#     _init_physical_input()
#     if _phys_input is None:
#         return False

#     now = time.monotonic()
#     try:
#         v = _phys_input.value
#     except Exception:
#         return False

#     # Initialize on first read
#     if _last_phys_state is None:
#         _last_phys_state = v
#         _last_phys_change_time = now

#     # State changed: update timestamp
#     if v != _last_phys_state:
#         _last_phys_state = v
#         _last_phys_change_time = now

#     # If stable for debounce_ms, update stable active flag
#     if (now - _last_phys_change_time) >= (debounce_ms / 1000.0):
#         # With pull-up, LOW (False) means activity
#         _last_stable_active = (not _last_phys_state)

#     return _last_stable_active


# Output pin for external HDD LED (lazy init)
_led_output = None


def _init_led_output():
    """Lazy-init GP10 as an output to drive an external HDD LED."""
    global _led_output
    if _led_output is not None:
        return
    try:
        d = digitalio.DigitalInOut(board.GP1)
        d.direction = digitalio.Direction.OUTPUT
        d.value = False
        _led_output = d
    except Exception:
        _led_output = None


def hdd_out(active):
    """Drive the external HDD LED on `GP10`.

    `active` is a boolean; True turns the LED on, False turns it off.
    The function is safe to call even if the hardware initialization
    fails (it will silently no-op).
    """
    _init_led_output()
    if _led_output is None:
        return
    try:
        _led_output.value = bool(active)
    except Exception:
        pass


def _get_simulated_access():
    global next_switch_time, current_access_state

    current_time = time.monotonic()

    # If the current time has passed our deadline, flip the switch
    if current_time >= next_switch_time:
        # 1. Pick a new random state
        current_access_state = random.choice([True, False])

        # 2. Pick a random duration between 0 and x seconds
        duration = random.uniform(0, 2)

        # 3. Set the new deadline
        next_switch_time = current_time + duration

    return current_access_state


def get_access():
    """Return current access state: simulated or physical depending on settings."""
    if settings.SIMULATION_MODE:
        return _get_simulated_access()
    return _detect_physical_access()