# isa_monitor_simple.py
# A CircuitPython program for the Raspberry Pi Pico
# to monitor ISA bus activity using simple pin monitoring.

import board
import digitalio
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

# --- Main Program Logic ---
print("Starting ISA bus monitor (simple pin monitoring)...")

# Configure the address pins as inputs with pull-up resistors
# to ensure a defined state when not being driven by the ISA bus.
addr_pins = []
for i in range(ADDR_PIN_COUNT):
    pin = digitalio.DigitalInOut(getattr(board, f"GP{i}"))
    pin.pull = digitalio.Pull.UP
    addr_pins.append(pin)

# Configure the control pins (IOR/IOW) as inputs with pull-up resistors
ior_pin = digitalio.DigitalInOut(getattr(board, f"GP{IOR_PIN}"))
ior_pin.pull = digitalio.Pull.UP

iow_pin = digitalio.DigitalInOut(getattr(board, f"GP{IOW_PIN}"))
iow_pin.pull = digitalio.Pull.UP

print("Monitoring for HDD, FDD, and Keyboard activity...")

# Variables for activity aggregation
hdd_activity_counter = 0
hdd_poll_counter = 0
activity_threshold = 20  # This value can be adjusted
last_activity_time = time.monotonic()

# Store previous states for edge detection
prev_ior_state = ior_pin.value
prev_iow_state = iow_pin.value

try:
    while True:
        current_time = time.monotonic()
        
        # Reset counters if there has been no activity for a while
        if (current_time - last_activity_time) > 0.05:  # 50ms in seconds
            if hdd_activity_counter > 0:
                print(" | ", end="")
            hdd_activity_counter = 0
            hdd_poll_counter = 0

        # Check for IOR activity (falling edge detection)
        current_ior_state = ior_pin.value
        if current_ior_state != prev_ior_state and current_ior_state == False:  # Falling edge
            # Read address bus when IOR goes low
            addr = 0
            for i, pin in enumerate(addr_pins):
                if pin.value:
                    addr |= (1 << i)
            
            print(f"IOR↓ Addr:0x{addr:03X}")  # Add this line
            
            last_activity_time = current_time
            if addr == 0x1F0:
                # Increment the data transfer counter
                hdd_activity_counter += 1
            elif addr == 0x1F7:
                # Increment the status poll counter
                hdd_poll_counter += 1
        
        prev_ior_state = current_ior_state

        # Check for IOW activity (falling edge detection)
        current_iow_state = iow_pin.value
        if current_iow_state != prev_iow_state and current_iow_state == False:  # Falling edge
            # Read address bus when IOW goes low
            addr = 0
            for i, pin in enumerate(addr_pins):
                if pin.value:
                    addr |= (1 << i)
            
            # print(f"IOW↓ Addr:0x{addr:03X}")  # Add this line
            
            last_activity_time = current_time
            if addr == 0x1F0:
                # Increment the data transfer counter
                hdd_activity_counter += 1
            elif addr == 0x1F7:
                # Increment the status poll counter
                hdd_poll_counter += 1
        
        prev_iow_state = current_iow_state

        # Check if the aggregated activity has exceeded the threshold
        if hdd_activity_counter > activity_threshold:
            print("H", end="")  # Print a single character for sustained HDD activity
            hdd_activity_counter = 0  # Reset the counter

        # Check if the aggregated poll activity has exceeded the threshold
        if hdd_poll_counter > activity_threshold:
            print("P", end="")  # Print a single character for sustained polling
            hdd_poll_counter = 0  # Reset the counter

        # A small delay to prevent the loop from running too hot
        time.sleep(0.001)  # 1ms in seconds

except KeyboardInterrupt:
    print("\nMonitor stopped.")
    
    # Clean up pins
    for pin in addr_pins:
        pin.deinit()
    ior_pin.deinit()
    iow_pin.deinit()

