import board
import analogio
import digitalio
import settings

# --- Calculated Internal Threshold ---
# Calculate the ratio: 2000 / (1000 + 2000) = 0.666
DIVIDER_RATIO = settings.POWER_RESISTOR_TO_GND / (settings.POWER_RESISTOR_TO_5V + settings.POWER_RESISTOR_TO_GND)

# Calculate what the ADC pin sees when external is at POWER_VOLTAGE_THRESHOLD_EXT
pin_voltage_target = settings.POWER_VOLTAGE_THRESHOLD_EXT * DIVIDER_RATIO

# Convert that pin voltage to the 0-65535 scale
ADC_THRESHOLD = int((pin_voltage_target / settings.POWER_ADC_REF_VOLTAGE) * settings.POWER_MAX_ADC_VALUE)

# Safety clip: ensure threshold doesn't exceed ADC limits
ADC_THRESHOLD = min(max(ADC_THRESHOLD, 0), settings.POWER_MAX_ADC_VALUE)

# --- Hardware Setup ---
usb_vbus = digitalio.DigitalInOut(board.VBUS_SENSE)
usb_vbus.direction = digitalio.Direction.INPUT
power_sense_adc = analogio.AnalogIn(settings.POWER_SENSE_PIN)

def is_usb_powered():
    return usb_vbus.value

def external_power():
    if not settings.POWER_DETECTION:
        return True # If power detection is disabled, assume we have external power

    if is_usb_powered():
        return True

    # Compare raw ADC value to our dynamically calculated threshold
    return power_sense_adc.value > ADC_THRESHOLD
