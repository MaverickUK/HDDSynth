import time

import settings
import nvm_wrapper


class PersistedFloat:
    """A 0.0-1.0 value adjusted in discrete steps and persisted to NVM with debounce.

    NVM byte values 0-100 map to 0.0-1.0; anything outside that range (e.g. an
    uninitialised 0xFF) is treated as missing and the default is used.
    """

    def __init__(self, default, step, nvm_address):
        self._step = step
        self._nvm_address = nvm_address
        self._dirty_since = None
        self._value = self._load_initial(default)

    def _load_initial(self, default):
        if not settings.NVM_PERSIST_VOLUME_BALANCE:
            return default
        raw = nvm_wrapper.safe_read(self._nvm_address)
        if raw is None or raw > 100:
            return default
        return raw / 100.0

    def adjust(self, steps):
        """Move the value by `steps * step`, clamped to [0, 1]. Returns True if it changed."""
        new_value = max(0.0, min(1.0, self._value + steps * self._step))
        if new_value == self._value:
            return False
        self._value = new_value
        self._dirty_since = time.monotonic()
        return True

    def get(self):
        return self._value

    def persist_if_due(self):
        """Write to NVM once the debounce window has elapsed."""
        if self._dirty_since is None or not settings.NVM_PERSIST_VOLUME_BALANCE:
            return
        if (time.monotonic() - self._dirty_since) >= settings.NVM_PERSIST_DEBOUNCE_S:
            nvm_wrapper.write(self._nvm_address, int(self._value * 100))
            self._dirty_since = None
