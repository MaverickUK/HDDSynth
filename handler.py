# Start PIO and then handle events raised (e.g. HDD read activity)

from machine import Pin
import rp2
import isa_monitor  # the file with PIO code
import time

# Define address input pins
addr_pins = [Pin(i, Pin.IN, Pin.PULL_DOWN) for i in range(10)]

# Define control line pins
ior = Pin(10, Pin.IN, Pin.PULL_UP)
iow = Pin(11, Pin.IN, Pin.PULL_UP)

# Install PIO program
sm = rp2.StateMachine(0, isa_monitor.isa_monitor,
                      in_base=addr_pins[0],
                      jmp_pin=ior,
                      freq=4_000_000)  # 4 MHz sampling

sm.active(1)

# Decode and handle events
def handle_event(data):
    addr = (data >> 1) & 0x3FF   # 10-bit address
    is_write = data & 0x1
    if is_write:
        print(f"Write to {hex(addr)}")
    else:
        print(f"Read from {hex(addr)}")

# Main loop
print("Listening for ISA events...")
while True:
    if sm.rx_fifo():
        data = sm.get()
        handle_event(data)
