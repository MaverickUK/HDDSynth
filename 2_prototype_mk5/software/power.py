import time
import analogio
import digitalio
import settings

# --- Calculated Divider Ratio ---
# Calculate the ratio: 22000 / (22000 + 22000) = 0.5
SUPERCAP_DIVIDER_RATIO = settings.SUPERCAP_RESISTOR_BOTTOM / (settings.SUPERCAP_RESISTOR_TOP + settings.SUPERCAP_RESISTOR_BOTTOM)

_SUPERCAP_SAMPLES = 16  # ADC reads averaged per supercap measurement

# --- Hardware Setup ---
# eFuse fault flag: open-drain, pulled up externally by R35, so no internal pull
power_fault = digitalio.DigitalInOut(settings.POWER_FAULT_PIN)
power_fault.direction = digitalio.Direction.INPUT

supercap_adc = analogio.AnalogIn(settings.SUPERCAP_SENSE_PIN)


def external_power():
    if not settings.POWER_DETECTION:
        return True # If power detection is disabled, assume we have external power

    # FLT is HIGH while the eFuse input is within its UV/OV window
    return power_fault.value


def supercap_voltage():
    """Supercap voltage in volts, averaged over a few ADC reads."""
    total = 0
    for _ in range(_SUPERCAP_SAMPLES):
        total += supercap_adc.value
    pin_voltage = (total / _SUPERCAP_SAMPLES / settings.POWER_MAX_ADC_VALUE) * settings.POWER_ADC_REF_VOLTAGE
    return pin_voltage / SUPERCAP_DIVIDER_RATIO


def wait_for_power_restored():
    """Block until external power has genuinely returned.

    FLT alone isn't trustworthy here: once the eFuse input decays below its own
    power-on threshold it can no longer hold FLT low, and R35 pulls the line back
    HIGH while we're still running from the supercap. So also require the
    supercap voltage to be rising, which only happens when the TPS61094 is
    charging from real input power.
    """
    if not settings.POWER_DETECTION:
        return

    baseline = supercap_voltage()
    window_start = time.monotonic()

    while True:
        time.sleep(0.1)
        voltage = supercap_voltage()

        if not power_fault.value:
            # Still faulted, so track the current level and start over
            baseline = voltage
            window_start = time.monotonic()
            continue

        # Use the lowest reading in the window so a draining cap never looks like a rise
        baseline = min(baseline, voltage)
        if voltage - baseline >= settings.SUPERCAP_RESTORE_RISE_V:
            print(f"[power] Power restored (supercap {baseline:.2f} V -> {voltage:.2f} V)")
            return

        if time.monotonic() - window_start >= settings.SUPERCAP_RESTORE_WINDOW_S:
            baseline = voltage
            window_start = time.monotonic()
