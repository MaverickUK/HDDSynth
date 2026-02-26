import microcontroller

import sample_cache
import sample_changer
import sdcard
import settings

desired_pack = sample_changer.get_desired_pack()

# TODO Refactor this to not be awful
pack_files = [f"{settings.SDCARD_SAMPLE_DIR}/{sample_changer.get_desired_pack()}/spinup.wav", f"{settings.SDCARD_SAMPLE_DIR}/{sample_changer.get_desired_pack()}/idle.wav", f"{settings.SDCARD_SAMPLE_DIR}/{sample_changer.get_desired_pack()}/access.wav"]

print(f"Desired pack: {desired_pack}")
print(f"Pack files: {pack_files}")

sdcard.initilise()    

sample_cache.update_cache_files(pack_files) # The file list doesn't matter, we just need to trigger the mode and reboot after caching.
