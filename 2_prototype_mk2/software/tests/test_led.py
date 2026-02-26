import board
import digitalio
import time

# 1. Setup the Optocoupler Input (GP26)
# Using Pull.UP: Inactive = True, Active = False
optocoupler = digitalio.DigitalInOut(board.GP26)
optocoupler.direction = digitalio.Direction.INPUT
optocoupler.pull = digitalio.Pull.UP

# 2. Setup the Onboard LED
pico_led = digitalio.DigitalInOut(board.LED)
pico_led.direction = digitalio.Direction.OUTPUT

# 3. Setup the External LED (GP1)
external_led = digitalio.DigitalInOut(board.GP1)
external_led.direction = digitalio.Direction.OUTPUT

print("Monitoring Optocoupler activity...")

while True:
    # Because of the Pull-Up, the logic is INVERTED:
    # If optocoupler.value is False, it means the optocoupler is active (GND).
    if not optocoupler.value:
        pico_led.value = True
        external_led.value = True
    else:
        pico_led.value = False
        external_led.value = False
    
    # Very small sleep to prevent "button bounce" or flickering
    time.sleep(0.01)