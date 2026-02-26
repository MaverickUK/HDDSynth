
import analogio

import settings

pot = analogio.AnalogIn(settings.POT_PIN)


def _get_volume_classic():
    # CircuitPython ADC values range from 0 to 65535
    raw_value = pot.value
    
    # Convert raw value (0-65535) to value between 0.0 and 1.0
    volume = raw_value / 65535

    return volume

# Track the previous level to detect changes
last_printed_level = -1 

def _get_volume_discrete():
    global last_printed_level
    
    # 1. Get raw value (0-65535)
    raw_value = pot.value
    
    # 2. Map to 0-X (Integer precision)
    # Using integer division // to strip decimals
    current_level = int((raw_value / 65535) * settings.VOLUME_DISCRETE_RANGE)
    
    # 3. Check if it changed
    if settings.VOLUME_PRINT and current_level != last_printed_level:
        print("Volume:", current_level, end="%\n") # Print with % and newline
        last_printed_level = current_level
        
    # 4. Convert back to 0.0 - 1.0 for the mixer
    return current_level / settings.VOLUME_DISCRETE_RANGE

def get_volume():
    if settings.VOLUME_DISCRETE:
        return _get_volume_discrete()
    else:
        return _get_volume_classic()
    