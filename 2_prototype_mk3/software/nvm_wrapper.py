import microcontroller
import time

### NVM flag values 
# Pico operating mode
MODE_USB = 0
MODE_WRITE = 1

# Jingle state
JINGLE_PLAYED = 1
JINGLE_NOT_PLAYED = 0

def write(address, value):
    microcontroller.nvm[address] = value

def safe_write(address, value, reset = False):
    microcontroller.nvm[address] = value
    time.sleep(0.5) # Allow NVM to settle

    if reset:
        microcontroller.reset()

def safe_read(address):
    """Reads a value from NVM at the specified address."""
    try:
        return microcontroller.nvm[address]
    except IndexError:
        print(f"[NVM] ERROR: Attempted to read from invalid NVM address {address}")
        return None
