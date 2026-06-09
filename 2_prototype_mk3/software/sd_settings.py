import json
import os

import settings
import sample_changer


def load_settings():
    """
    Load settings from /sd/settings.json if it exists.
    Returns a dict with any overridden settings.
    Returns empty dict if file doesn't exist or SD card is not available.
    """
    settings_file = f"{settings.SDCARD_MOUNT_POINT}/settings.json"

    try:
        if not os.path.exists(settings_file):
            return {}

        with open(settings_file, 'r') as f:
            data = json.load(f)

        print(f"[SD Settings] Loaded settings from {settings_file}")
        return data
    except (OSError, json.JSONDecodeError) as e:
        print(f"[SD Settings] Error loading settings: {e}")
        return {}


def get_sample_pack_from_sd(sd_settings):
    """
    Get the sample pack name from SD settings.
    Returns None if not specified in SD settings.
    """
    return sd_settings.get("SAMPLE_PACK")


def install_sample_pack_if_needed(sd_settings):
    """
    If SAMPLE_PACK is specified in SD settings and differs from current,
    attempt to install it. Returns True if successful or no change needed,
    False if pack not found on SD card.
    """
    pack_name = get_sample_pack_from_sd(sd_settings)

    if not pack_name:
        return True

    current_pack = sample_changer.get_desired_pack()

    if current_pack == pack_name:
        print(f"[SD Settings] Sample pack already installed: {pack_name}")
        return True

    # Check if the pack exists on SD card
    pack_path = f"{settings.SDCARD_SAMPLE_DIR}/{pack_name}"

    try:
        if not os.path.exists(pack_path):
            print(f"[SD Settings] Sample pack not found: {pack_path}")
            return False

        # Pack exists, set it as desired
        print(f"[SD Settings] Installing sample pack: {pack_name}")
        sample_changer.set_desired_pack(pack_name)

        # Trigger cache update for new pack
        import sample_cache
        sample_cache.trigger_write_mode()

        return True
    except OSError:
        print(f"[SD Settings] Error accessing sample pack directory")
        return False
