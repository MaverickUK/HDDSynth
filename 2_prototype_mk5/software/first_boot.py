import board
import digitalio

import nvm_wrapper
import rgb_led
import sample_changer
import sdcard
import settings


def run_if_needed():
    """Run first-time setup if NVM is uninitialised (blank Pico).

    On completion, writes NVM_MODE_WRITE and resets the Pico so the normal
    write-mode cache path runs on the next boot. Never returns if first boot
    is detected.
    """
    mode = nvm_wrapper.safe_read(settings.NVM_ADDRESS_MODE)
    if mode in (settings.NVM_MODE_USB, settings.NVM_MODE_WRITE):
        return

    print("[FirstBoot] Blank NVM detected — running first-time setup...")

    led = digitalio.DigitalInOut(board.LED)
    led.direction = digitalio.Direction.OUTPUT
    led.value = True

    rgb_led.busy_tick()
    sdcard.initialise()
    rgb_led.busy_tick()
    sample_changer.wipe_settings()
    rgb_led.busy_tick()
    sample_changer.initialize()
    rgb_led.busy_end()

    nvm_wrapper.safe_write(settings.NVM_ADDRESS_JINGLE, settings.NVM_JINGLE_NOT_PLAYED)
    nvm_wrapper.safe_write(settings.NVM_ADDRESS_MODE, settings.NVM_MODE_WRITE, reset=True)
    # reset=True causes microcontroller.reset() — execution never reaches here
