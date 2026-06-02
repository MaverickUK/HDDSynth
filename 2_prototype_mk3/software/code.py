import settings
import gpio_safety

# Pull unused GPIOs low before any peripheral modules claim their pins.
if settings.PULL_DOWN_UNUSED_GPIOS:
    gpio_safety.pull_down_unused(settings.USED_GPIO_PINS)

import board
import digitalio
import first_boot
import hddsynth
import nvm_wrapper
import sample_cache
import sample_changer
import sdcard

# Auto-detect a blank Pico and run first-time setup (resets on completion).
first_boot.run_if_needed()

mode = nvm_wrapper.safe_read(settings.NVM_ADDRESS_MODE)

if mode == settings.NVM_MODE_WRITE:
    # Write Mode: cache the requested HDD sample pack
    try:
        led = digitalio.DigitalInOut(board.LED)
        led.direction = digitalio.Direction.OUTPUT
        led.value = True

        desired_pack = sample_changer.get_desired_pack()
        base_path = f"{settings.SDCARD_SAMPLE_DIR}/{desired_pack}"

        # TODO: Refactor this
        pack_files = [
            f"{base_path}/spinup.wav",
            f"{base_path}/spindown.wav",
            f"{base_path}/idle.wav",
            f"{base_path}/access.wav",
        ]

        sdcard.initialise()
        sample_cache.update_cache_files(pack_files)
    finally:
        sample_cache.trigger_usb_mode()  # Fail safe, always revert to USB
else:
    # Normal operation (USB mode)
    print("Running in USB mode, normal operation")
    hddsynth.run_synth()
