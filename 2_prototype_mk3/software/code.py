import digitalio
import board

import sample_cache
import sample_changer
import sdcard
import hddsynth
import settings
import nvm_wrapper

mode = nvm_wrapper.safe_read(settings.NVM_ADDRESS_MODE)

if mode == settings.NVM_MODE_WRITE:
    # Write Mode: cache the requested HDD sample pack
    try:
        # Pico LED on to indicate write mode is active
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
    # Anything other than WRITE (including USB and uninitialised NVM) → normal operation
    print("Running in USB mode, normal operation")
    hddsynth.run_synth()
