import microcontroller
import digitalio
import board

import sample_cache
import sample_changer
import sdcard
import hddsynth
import settings
import nvm_wrapper

# We are in USB mode (Normal operation)
if microcontroller.nvm[settings.NVM_ADDRESS_MODE] == nvm_wrapper.MODE_USB:
    print("Running in USB mode, normal operation")
    hddsynth.run_synth()

# We are in Write Mode, cache the requested HDD Sample Pack
if microcontroller.nvm[settings.NVM_ADDRESS_MODE] == nvm_wrapper.MODE_WRITE:
    try:
        # Pico LED
        led = digitalio.DigitalInOut(board.LED)
        led.direction = digitalio.Direction.OUTPUT
        led.value = True  # Turn on LED to indicate write mode is active

        desired_pack = sample_changer.get_desired_pack()

        base_path = f"{settings.SDCARD_SAMPLE_DIR}/{sample_changer.get_desired_pack()}"

        # TODO: Refactor this        
        pack_files = [
            f"{base_path}/spinup.wav", 
            f"{base_path}/spindown.wav", 
            f"{base_path}/idle.wav", 
            f"{base_path}/access.wav"
        ]

        sdcard.initilise()    
        sample_cache.update_cache_files(pack_files)
    finally:
        sample_cache.trigger_usb_mode() # Fail safe, always revert to USB