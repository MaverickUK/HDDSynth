import time
import power
import settings

# Bench check for the eFuse fault flag and supercap sensing.
# Plug and unplug USB while this runs to watch FLT and the supercap voltage.
print(f"Supercap full charge: {settings.SUPERCAP_FULL_V} V")

while True:
    print(
        "FLT OK:", power.power_fault.value,
        "| Supercap raw ADC:", power.supercap_adc.value,
        f"| Supercap: {power.supercap_voltage():.2f} V",
    )
    time.sleep(0.25)
