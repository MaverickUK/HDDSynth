import power

print('Raw power sense ADC:', power.power_sense_adc.value, '/ threshold:', power.ADC_THRESHOLD)

print('Is External Power Detected:', power.external_power())