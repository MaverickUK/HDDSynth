import time

import settings
import nvm_wrapper


def _load_initial():
    if not settings.NVM_PERSIST_VOLUME_BALANCE:
        return settings.VOLUME_DEFAULT
    raw = nvm_wrapper.safe_read(settings.NVM_ADDRESS_VOLUME)
    if raw is None or raw > 100:
        return settings.VOLUME_DEFAULT
    return raw / 100.0


_volume = _load_initial()
_dirty_since = None


def adjust(steps):
    """Adjust volume by `steps` encoder detents (positive = louder)."""
    global _volume, _dirty_since
    new_volume = max(0.0, min(1.0, _volume + steps * settings.VOLUME_STEP))
    if new_volume != _volume:
        _volume = new_volume
        _dirty_since = time.monotonic()
        if settings.VOLUME_PRINT:
            print(f"Volume: {int(_volume * 100)}%")


def get_volume():
    return _volume


def persist_if_due():
    """Write the current volume to NVM once the debounce window has elapsed."""
    global _dirty_since
    if _dirty_since is None or not settings.NVM_PERSIST_VOLUME_BALANCE:
        return
    if (time.monotonic() - _dirty_since) >= settings.NVM_PERSIST_DEBOUNCE_S:
        nvm_wrapper.write(settings.NVM_ADDRESS_VOLUME, int(_volume * 100))
        _dirty_since = None
