import microcontroller
import time

# How long to wait after an NVM write so the flash can settle.
_SETTLE_S = 0.5


def write(address, value):
    microcontroller.nvm[address] = value


def safe_write(address, value, reset=False):
    microcontroller.nvm[address] = value
    time.sleep(_SETTLE_S)

    if reset:
        microcontroller.reset()


def write_bytes(start, data):
    """Write a byte slice and sleep for NVM to settle."""
    microcontroller.nvm[start : start + len(data)] = data
    time.sleep(_SETTLE_S)


def safe_read(address):
    """Reads a value from NVM at the specified address."""
    try:
        return microcontroller.nvm[address]
    except IndexError:
        print(f"[NVM] ERROR: Attempted to read from invalid NVM address {address}")
        return None


def read_bytes(start, length):
    """Reads `length` bytes starting at `start` from NVM."""
    return microcontroller.nvm[start : start + length]
