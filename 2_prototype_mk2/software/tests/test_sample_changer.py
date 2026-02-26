import microcontroller

import sample_changer
import sample_cache
import sdcard
import settings

# Initilise the SD card for samples storage
sdcard.initilise()

# sample_changer.wipe_settings()
sample_changer.initialize()


# sample_cache.trigger_usb_mode()
target_mode = microcontroller.nvm[settings.NVM_ADDRESS_MODE]

print(f"Target mode: {target_mode} (1 = Write, 0 = USB)")

desired_pack = sample_changer.get_desired_pack()
# current_pack = sample_changer.get_current_pack()

# print(f"current pack: {current_pack}")
print(f"desired pack: {desired_pack}")

sample_changer.next_pack()