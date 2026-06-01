# boot.py
import storage
import board
import digitalio

import settings
import nvm_wrapper

# Boot runs when the Pi Pico is switched on before anything else.
# We use it to check a flag in NVM to determine if we should be in USB mode (normal) or Write Mode (for caching files).

# Setup a safety pin (e.g., GP0). If held LOW at boot, force USB mode.
# This prevents getting locked out if your code crashes in Write Mode.
safety_pin = digitalio.DigitalInOut(board.GP0)
safety_pin.switch_to_input(pull=digitalio.Pull.UP)


# Check the persistent state flag (Byte 0 of NVM)
target_mode = nvm_wrapper.safe_read(settings.NVM_ADDRESS_MODE)
if target_mode is None:
    target_mode = settings.NVM_MODE_USB

if target_mode not in (settings.NVM_MODE_USB, settings.NVM_MODE_WRITE):
    print(f"[Cache] WARNING: Unrecognized NVM state ({target_mode}), defaulting to USB mode.")
    target_mode = settings.NVM_MODE_USB


# If safety pin is pressed (LOW), force USB mode
if not safety_pin.value:
    print("Safety pin detected: Forcing USB Mode")
    storage.remount("/", True)
    nvm_wrapper.write(settings.NVM_ADDRESS_MODE, settings.NVM_MODE_USB)  # Reset flag

elif target_mode == settings.NVM_MODE_WRITE:
    print("Booting in DRIVE Mode (Code can write)")
    storage.remount("/", False)
else:
    # Default USB Mode
    print("Booting in USB Mode (Code cannot write)")
    storage.remount("/", True)
