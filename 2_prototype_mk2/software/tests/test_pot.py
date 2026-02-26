# Test of volume control pot

import board
import analogio
import time

# Initialize the potentiometer on GP27 (ADC1)
pot = analogio.AnalogIn(board.GP27)

print("Potentiometer Test Starting...")
print("Rotate the pot to see values from 0% to 100%")
print("-" * 40)

while True:
    # CircuitPython ADC values range from 0 to 65535
    raw_value = pot.value
    
    # Convert raw value (0-65535) to percentage (0-100)
    percentage = (raw_value / 65535) * 100
    
    # Use :.1f to show one decimal point for smoothness
    print(f"Raw: {raw_value:5d} | Volume: {percentage:5.1f}%")
    
    time.sleep(0.1)