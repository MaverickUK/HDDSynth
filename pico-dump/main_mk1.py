# isa_monitor.py
# A MicroPython program for the Raspberry Pi Pico
# to monitor ISA bus activity using PIO.

import rp2
from machine import Pin
import time

# --- Hardware Configuration ---
# Assuming ISA address lines A0-A9 are connected to GPIO 0-9.
# Assuming ISA IOR signal is on GPIO 10.
# Assuming ISA IOW signal is on GPIO 11.
# The user specified 12 pins (0-11) for this setup.

# Define the pins for the address bus (A0-A9) and control signals (IOR/IOW)
ADDR_PIN_BASE = 0
ADDR_PIN_COUNT = 10
IOR_PIN = 10
IOW_PIN = 11

# --- PIO Program Definitions ---
# The PIO program is designed to be very simple and fast.
# It waits for a control pin (IOR or IOW) to go low, then captures the
# 10 address lines and pushes the value to the RX FIFO.
# This offloads the high-speed bus monitoring from the main Python thread.

@rp2.asm_pio(
    in_shiftdir=rp2.PIO.SHIFT_LEFT,  # Shift bits from LSB to MSB (A0 to A9)
    autopush=True,                  # Automatically push to FIFO when ISR is full
    push_thresh=10,                 # Push when 10 bits are in ISR
    fifo_join=rp2.PIO.JOIN_RX       # Join FIFOs to get more RX space
)
def ior_pio_program():
    """PIO program for detecting I/O Read (IOR) activity."""
    # Wait for the IOR pin to go low (active low)
    # The `jmp_pin` is configured in the StateMachine, so we use index 0.
    wrap_target()
    wait(0, pin, 0)

    # Read the 10 address pins (A0-A9) and shift them into the ISR.
    # We use a hardcoded value `10` because the PIO assembler can't use Python variables.
    in_(pins, 10)

    # We don't need to push manually because `autopush` is enabled.
    wrap()

@rp2.asm_pio(
    in_shiftdir=rp2.PIO.SHIFT_LEFT,
    autopush=True,
    push_thresh=10,
    fifo_join=rp2.PIO.JOIN_RX
)
def iow_pio_program():
    """PIO program for detecting I/O Write (IOW) activity."""
    # Wait for the IOW pin to go low (active low)
    # The `jmp_pin` is configured in the StateMachine, so we use index 0.
    wrap_target()
    wait(0, pin, 0)

    # Read the 10 address pins (A0-A9) and shift them into the ISR.
    # We use a hardcoded value `10` because the PIO assembler can't use Python variables.
    in_(pins, 10)
    wrap()

# --- Main Program Logic ---
print("Starting ISA bus monitor...")

# Configure the address pins as inputs with pull-up resistors
# to ensure a defined state when not being driven by the ISA bus.
addr_pins = [Pin(i, Pin.IN, Pin.PULL_UP) for i in range(ADDR_PIN_COUNT)]

# Configure the control pins (IOR/IOW) as inputs with pull-up resistors
ior_pin = Pin(IOR_PIN, Pin.IN, Pin.PULL_UP)
iow_pin = Pin(IOW_PIN, Pin.IN, Pin.PULL_UP)

# Create and configure the state machines
# sm0 monitors IOR activity
sm_ior = rp2.StateMachine(
    0,
    ior_pio_program,
    freq=1_000_000,
    in_base=Pin(ADDR_PIN_BASE),
    jmp_pin=ior_pin
)

# sm1 monitors IOW activity
sm_iow = rp2.StateMachine(
    1,
    iow_pio_program,
    freq=1_000_000,
    in_base=Pin(ADDR_PIN_BASE),
    jmp_pin=iow_pin
)

# Start both state machines
sm_ior.active(1)
sm_iow.active(1)

print("Monitoring for HDD, FDD, and Keyboard activity...")

try:
    while True:
        # Check for data from the IOR state machine's FIFO
        if sm_ior.rx_fifo() > 0:
            addr = sm_ior.get()
            # Check the address to see which device it corresponds to
            if (addr >= 0x1F0 and addr <= 0x1F7) or addr == 0x3F6:
                print("h", end="")  # HDD Read
            elif (addr >= 0x3F0 and addr <= 0x3F7):
                print("f", end="")  # FDD Read
            elif addr == 0x60 or addr == 0x64:
                print("k", end="")  # Keyboard Read

        # Check for data from the IOW state machine's FIFO
        if sm_iow.rx_fifo() > 0:
            addr = sm_iow.get()
            # Check the address to see which device it corresponds to
            if (addr >= 0x1F0 and addr <= 0x1F7) or addr == 0x3F6:
                print("H", end="")  # HDD Write
            elif (addr >= 0x3F0 and addr <= 0x3F7):
                print("F", end="")  # FDD Write
            elif addr == 0x60 or addr == 0x64:
                print("K", end="")  # Keyboard Write

        # A small delay to prevent the loop from running too hot,
        # though the PIO will handle events independently.
        time.sleep_ms(1)

except KeyboardInterrupt:
    print("\nMonitor stopped.")
    sm_ior.active(0)
    sm_iow.active(0)
