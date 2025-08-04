import machine
import time

# Define GPIO pins for address (A0-A2), data (D0-D7), and control lines
ADDRESS_PINS = [
    machine.Pin(0, machine.Pin.OUT),  # A0
    machine.Pin(1, machine.Pin.OUT),  # A1
    machine.Pin(2, machine.Pin.OUT),  # A2
]

DATA_PINS = [
    machine.Pin(8, machine.Pin.IN),   # D0
    machine.Pin(9, machine.Pin.IN),   # D1
    machine.Pin(10, machine.Pin.IN),  # D2
    machine.Pin(11, machine.Pin.IN),  # D3
    machine.Pin(12, machine.Pin.IN),  # D4
    machine.Pin(13, machine.Pin.IN),  # D5
    machine.Pin(14, machine.Pin.IN),  # D6
    machine.Pin(15, machine.Pin.IN),  # D7
]

IOR_PIN = machine.Pin(16, machine.Pin.OUT)  # IOR#
CS_PIN = machine.Pin(17, machine.Pin.OUT)   # Chip select, if needed

def set_address(addr):
    for i, pin in enumerate(ADDRESS_PINS):
        pin.value((addr >> i) & 1)

def read_port(base_addr, reg_offset=0):
    set_address(reg_offset)
    CS_PIN.value(0)      # Assert chip select (if needed)
    IOR_PIN.value(0)     # Assert IOR#
    time.sleep_us(1)     # Small delay for bus timing
    data = 0
    for i, pin in enumerate(DATA_PINS):
        data |= (pin.value() << i)
    IOR_PIN.value(1)     # Deassert IOR#
    CS_PIN.value(1)      # Deassert chip select
    return data

# IDE status register offset is 7 (0x1F7 or 0x177)
STATUS_REG_OFFSET = 7

def hdd_active(status):
    # Bit 7 (BUSY) or Bit 3 (DRQ) indicate activity
    return (status & 0x80) or (status & 0x08)

# IDE controller base addresses
PRIMARY_BASE = 0x1f0
SECONDARY_BASE = 0x170

print("Monitoring HDD activity. Press Ctrl+C to stop.")
try:
    while True:
        primary_status = read_port(PRIMARY_BASE, STATUS_REG_OFFSET)
        secondary_status = read_port(SECONDARY_BASE, STATUS_REG_OFFSET)
        if hdd_active(primary_status) or hdd_active(secondary_status):
            print(".", end="", flush=True)
        time.sleep(0.01)  # Poll every 10ms
except KeyboardInterrupt:
    print("\nStopped monitoring.")