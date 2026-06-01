import time

import settings
import nvm_wrapper


def _load_initial():
    if not settings.NVM_PERSIST_VOLUME_BALANCE:
        return settings.BALANCE_DEFAULT
    raw = nvm_wrapper.safe_read(settings.NVM_ADDRESS_BALANCE)
    if raw is None or raw > 100:
        return settings.BALANCE_DEFAULT
    return raw / 100.0


_balance = _load_initial()
_dirty_since = None


def adjust(steps):
    """Adjust balance by `steps` encoder detents (positive = more access)."""
    global _balance, _dirty_since
    new_balance = max(0.0, min(1.0, _balance + steps * settings.BALANCE_STEP))
    if new_balance != _balance:
        _balance = new_balance
        _dirty_since = time.monotonic()
        if settings.BALANCE_PRINT:
            print(f"Balance: {int(_balance * 100)}% access")


def get_balance():
    """0.0 = idle only, 1.0 = access only, 0.5 = equal mix."""
    return _balance


def persist_if_due():
    """Write the current balance to NVM once the debounce window has elapsed."""
    global _dirty_since
    if _dirty_since is None or not settings.NVM_PERSIST_VOLUME_BALANCE:
        return
    if (time.monotonic() - _dirty_since) >= settings.NVM_PERSIST_DEBOUNCE_S:
        nvm_wrapper.write(settings.NVM_ADDRESS_BALANCE, int(_balance * 100))
        _dirty_since = None
