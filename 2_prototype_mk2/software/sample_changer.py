import os
import time
import microcontroller

import settings
import sample_cache

def initialize():
    """
    Checks if NVM values are set. If not, picks the first 
    available directory from the SD card as the default.
    """
    current = get_desired_pack()
    
    # If desired is empty, we've never run this or NVM was cleared
    if not current:
        print("[Changer] NVM empty. Performing first-time setup...")
        try:
            print(f"Scanning {settings.SDCARD_SAMPLE_DIR} for sample packs...")
            all_items = os.listdir(settings.SDCARD_SAMPLE_DIR)

            packs = sorted([
                f for f in all_items 
                if _is_dir(f"{settings.SDCARD_SAMPLE_DIR}/{f}") and not f.startswith(".") # Ignore hidden directories
            ])
            
            if packs:
                first_pack = packs[0]
                set_desired_pack(first_pack)
                print(f"[Changer] Default pack set to: {first_pack}")
            else:
                print("[Changer] Warning: No packs found on SD during init.")
        except OSError:
            print("[Changer] Error: SD card not available during init.")
    else:
        print(f"[Changer] Initialization complete. Desired target: {get_desired_pack()}")

def wipe_settings():
    """
    Clears the Current and Desired NVM slots.
    """
    print("[Changer] Wiping NVM sample pack settings...")
    
    # Create a block of 128 null bytes (64 for Current + 64 for Desired)
    empty_block = b'\x00' * (settings.NVM_PACK_LENGTH * 2)
    
    # Write the block starting from index 2
    microcontroller.nvm[settings.NVM_ADDRESS_START_PACK_CURRENT : settings.NVM_ADDRESS_START_PACK_CURRENT + (settings.NVM_PACK_LENGTH * 2)] = empty_block
    
    print("[Changer] Wipe complete.")

def next_pack(reboot_after=True):
    """Scans SD, determines the next alphabetical pack, and sets it as desired."""
    try:
        # Get directories, sorted alphabetically
        all_items = os.listdir(settings.SDCARD_SAMPLE_DIR)
        packs = sorted([
            f for f in all_items 
            if _is_dir(f"{settings.SDCARD_SAMPLE_DIR}/{f}") and not f.startswith(".") # Ignore hidden directories
        ])
    except OSError:
        print("[Changer] Error: SD not accessible.")
        return

    if not packs:
        print("[Changer] No packs found.")
        return

    # Determine next pack
    current_desired = get_desired_pack()
    
    if current_desired in packs:
        next_index = (packs.index(current_desired) + 1) % len(packs)
    else:
        next_index = 0
    
    new_selection = packs[next_index]
    set_desired_pack(new_selection)
    print(f"[Changer] Target set to: {new_selection}")

    if reboot_after:
        sample_cache.trigger_write_mode()
        

# --- Public Abstraction Methods ---

def get_desired_pack():
    """Reads the 'Desired' pack name from NVM."""
    return _read_nvm_str(settings.NVM_ADDRESS_START_PACK_DESIRED)

def set_desired_pack(name):
    """Writes the 'Desired' pack name to NVM."""
    _write_nvm_str(settings.NVM_ADDRESS_START_PACK_DESIRED, name)

# --- Private Helpers ---

def _is_dir(path):
    try:
        return (os.stat(path)[0] & 0x4000) != 0
    except OSError:
        return False

def _write_nvm_str(start, text):
    """Encodes string and pads with null bytes to clear previous data."""
    encoded = text.encode('utf-8')[:settings.NVM_PACK_LENGTH]
    padded = encoded + b'\x00' * (settings.NVM_PACK_LENGTH - len(encoded))
    microcontroller.nvm[start : start + settings.NVM_PACK_LENGTH] = padded
    time.sleep(0.5) # Allow NVM to settle after write

def _read_nvm_str(start):
    """Reads bytes and stops at the first null terminator."""
    raw = microcontroller.nvm[start : start + settings.NVM_PACK_LENGTH]
    end = raw.find(b'\x00')
    if end == -1: end = settings.NVM_PACK_LENGTH
    try:
        return raw[:end].decode('utf-8').strip()
    except UnicodeError:
        return ""