print("Hello World!")

import board
import digitalio
import time

# Set up the internal LED pin
led = digitalio.DigitalInOut(board.LED)
led.direction = digitalio.Direction.OUTPUT

print("Blinking started! Press Ctrl+C to stop.")

while True:
    led.value = True   # Turn LED on
    print("LED ON")
    time.sleep(1.0)    # Wait for 1 second
    
    led.value = False  # Turn LED off
    print("LED OFF")
    time.sleep(1.0)    # Wait for 1 second