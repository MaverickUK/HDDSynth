from machine import Pin
import rp2
import isa_monitor
import time

# Define address input pins (A0–A9)
addr_pins = [Pin(i, Pin.IN, Pin.PULL_DOWN) for i in range(10)]

# Control lines: /IOR and /IOW
ior = Pin(10, Pin.IN, Pin.PULL_UP)
iow = Pin(11, Pin.IN, Pin.PULL_UP)

# Start state machine
sm = rp2.StateMachine(0, isa_monitor.isa_monitor,
                      in_base=addr_pins[0],
                      jmp_pin=ior,
                      freq=4_000_000)  # 4 MHz

sm.active(1)

# Address-to-device map
def detect_device(addr):
    if 0x1F0 <= addr <= 0x1F7 or addr == 0x3F6:
        return "HDD"
    elif 0x3F0 <= addr <= 0x3F7:
        return "FDD"
    elif addr == 0x60 or addr == 0x64:
        return "KBD"
    else:
        return None

# Interpret and handle events
def handle_event(data):
    addr = (data >> 1) & 0x3FF  # 10-bit address
    is_write = data & 0x1
    device = detect_device(addr)
    if device:
        direction = "W" if is_write else "R"
        if device == "HDD":
            print(f"[HDD-{direction}] Access at {hex(addr)}")
        elif device == "FDD":
            print(f"[FDD-{direction}] Access at {hex(addr)}")
        elif device == "KBD":
            print(f"[KBD-{direction}] Access at {hex(addr)}")
    # Optional: print unmatched accesses
    # else:
    #     print(f"Unknown {'W' if is_write else 'R'} at {hex(addr)}")

# Main loop
print("Monitoring ISA bus for HDD/FDD/Keyboard...")
while True:
    if sm.rx_fifo():
        data = sm.get()
        handle_event(data)
