
import board
import analogio


# Initialize the potentiometer on GP27 (ADC1)
pot = analogio.AnalogIn(board.GP27)

def get_volume():
    # CircuitPython ADC values range from 0 to 65535
    raw_value = pot.value
    
    # Convert raw value (0-65535) to percentage (0-100)
    # percentage = (raw_value / 65535) * 100
    volume = raw_value / 65535

    # Use :.1f to show one decimal point for smoothness
    # print(f"Raw: {raw_value:5d} | Volume: {percentage:5.1f}%")
    return volume
