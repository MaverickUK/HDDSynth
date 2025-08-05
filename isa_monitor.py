# State machine that watches /IOR and /IOW. When one of them goes low (active), the state machine reads the address lines and encodes a message.

from machine import Pin
import rp2
import array

@rp2.asm_pio(in_shiftdir=rp2.PIO.SHIFT_LEFT, autopull=False, autopush=True, push_thresh=16)
def isa_monitor():
    # Wait for /IOR low (active)
    wait(0, pin, 10)
    # Label as a read event
    set(x, 0)          # x = 0 (read)
    in_(pins, 10)      # Read A0–A9 (10 bits) into ISR
    in_(x, 1)          # Add 1 bit for direction = read
    push()

    # Wait for /IOR high again (debounce)
    wait(1, pin, 10)

    # Wait for /IOW low
    wait(0, pin, 11)
    set(x, 1)          # x = 1 (write)
    in_(pins, 10)      # Read A0–A9
    in_(x, 1)          # Add direction bit
    push()

    # Wait for /IOW high
    wait(1, pin, 11)

    # Loop
    jmp(isa_monitor)
