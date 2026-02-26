import microcontroller
import digitalio
import board

import sample_cache
import sample_changer
import sdcard
import hddsynth
import settings

# Ensure NVM initlised
#try:
#    sample_changer.initialize()
#except Exception as e:
#    print(f"[Boot] Error during sample changer initialization: {e}")


# Only trigger if we are in USB mode (Normal operation)
# AND some condition is met (e.g., a button press or a network flag)
if microcontroller.nvm[settings.NVM_ADDRESS_MODE] == sample_cache.MODE_USB:
    print("Running in USB mode, normal operation")
    hddsynth.run_synth()

# If we are in Write Mode (nvm[0] == 1), we MUST run the cache logic
# so it can finish the job and revert the mode.
if microcontroller.nvm[settings.NVM_ADDRESS_MODE] == sample_cache.MODE_WRITE:
     # The list here doesn't matter as much if you store the list in a temp file, 
     # but typically you define the list in code.py
     #files_to_copy = ["/sd/config.json", "/sd/image.bmp"]
     #cache.update_cache_files(files_to_copy)

    # try:
    #     print("Running in Write mode, starting cache update...")
    #     sdcard.initilise()

    #     files_to_cache = ["/sd/test.txt"]    
    #     sample_cache.update_cache_files(files_to_cache)
    # finally:
    #     sample_cache.trigger_usb_mode()

    try:
        # Pico LED
        led = digitalio.DigitalInOut(board.LED)
        led.direction = digitalio.Direction.OUTPUT
        led.value = True  # Turn on LED to indicate write mode is active

        # We should only be in WRITE mode if a change HDD Sample Pack operation was triggered
        desired_pack = sample_changer.get_desired_pack()

        # TODO Refactor this to not be awful
        pack_files = [f"{settings.SDCARD_SAMPLE_DIR}/{sample_changer.get_desired_pack()}/spinup.wav", f"{settings.SDCARD_SAMPLE_DIR}/{sample_changer.get_desired_pack()}/idle.wav", f"{settings.SDCARD_SAMPLE_DIR}/{sample_changer.get_desired_pack()}/access.wav"]

        sdcard.initilise()    

        sample_cache.update_cache_files(pack_files)
    finally:
        sample_cache.trigger_usb_mode() # Fail safe, always revert to USB