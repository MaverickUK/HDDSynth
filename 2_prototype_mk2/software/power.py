import board
import analogio
import digitalio
import settings

# --- Hardware Constants ---
RESISTOR_TO_5V = 1000   # 1k Ohm
RESISTOR_TO_GND = 2000  # 2k Ohm
ADC_REF_VOLTAGE = 3.3   # Pico's internal reference
MAX_ADC_VALUE = 65535   # CircuitPython 16-bit scaling

# --- User Setting ---
# Change this to whatever external voltage (0V-5V) you want to trigger at
# TODO: Move this to settings
VOLTAGE_THRESHOLD_EXT = 4.6 

# --- Calculated Internal Threshold ---
# Calculate the ratio: 2000 / (1000 + 2000) = 0.666
DIVIDER_RATIO = RESISTOR_TO_GND / (RESISTOR_TO_5V + RESISTOR_TO_GND)

# Calculate what the ADC pin sees when external is at VOLTAGE_THRESHOLD_EXT
pin_voltage_target = VOLTAGE_THRESHOLD_EXT * DIVIDER_RATIO

# Convert that pin voltage to the 0-65535 scale
ADC_THRESHOLD = int((pin_voltage_target / ADC_REF_VOLTAGE) * MAX_ADC_VALUE)

# Safety clip: ensure threshold doesn't exceed ADC limits
ADC_THRESHOLD = min(max(ADC_THRESHOLD, 0), MAX_ADC_VALUE)

# --- Hardware Setup ---
usb_vbus = digitalio.DigitalInOut(board.VBUS_SENSE)
usb_vbus.direction = digitalio.Direction.INPUT
power_sense_adc = analogio.AnalogIn(board.GP28) #TODO Move the GP to settings

def is_usb_powered():
    return usb_vbus.value

def external_power():
    if not settings.POWER_DETECTION:
        return True # If power detection is disabled, assume we have external power

    if is_usb_powered():
        return True
    
    # Compare raw ADC value to our dynamically calculated threshold
    return power_sense_adc.value > ADC_THRESHOLD
