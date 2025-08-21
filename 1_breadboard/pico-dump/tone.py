#
# MicroPython code for Raspberry Pi Pico with Pico Audio Pack
# Plays a continuous sine wave tone using standard I2S pins.
#
# This code assumes the Pico Audio Pack is connected via I2S,
# and it uses pins GP9, GP10, and GP11, which are also valid
# for direct connection to the Pico.
#
# Note: The Pico Audio Pack's standard configuration is mono,
# so only a single data pin (SD) is required.
#

import array
import math
import utime
from machine import Pin, I2S

# --- Standard Pin Definitions ---
# These pins are the default ones used when a Pi Pico is directly
# connected to the Pico Audio Pack.
BCK_PIN = Pin(26)  # Bit Clock (SCK)
WS_PIN = Pin(27)   # Word Select (WS)
SD_PIN  = Pin(28)   # Serial Data (SD)
MUTE_PIN = Pin(22) # Mute pin for the amplifier

# Due to GPIO 0 - 11 being used for ISA address bus monitoring, redirecting to use these pins
# Bit Clock (BCK): BCK_PIN = Pin(26) (Physical Pin 31)
# Word Select (WS): WS_PIN = Pin(27) (Physical Pin 32)
# Serial Data (SD): SD_PIN = Pin(28) (Physical Pin 34)
# Mute Pin: MUTE_PIN = Pin(22) (Physical Pin 29) - Any free GPIO will work here.

# --- Audio Configuration ---
SAMPLE_RATE = 22050  # Sample rate in Hz. A common value for digital audio.
BITS_PER_SAMPLE = 16 # Bits per sample. The Pico Audio Pack supports 16-bit.
BUFFER_LENGTH = 1000 # Length of the audio buffer in samples.
TONE_FREQUENCY = 440 # The frequency of the tone in Hz (A4 note).

# --- I2S Peripheral Setup ---
# Initialize the I2S peripheral with the standard pins and audio configuration.
# The `mode` is set to `I2S.TX` for transmit (sending audio out).
# `mono` is set to True as the Pico Audio Pack is a mono output device.
audio_out = I2S(
    0,                                     # I2S bus ID (0 or 1)
    sck=BCK_PIN,                           # Bit clock pin
    ws=WS_PIN,                             # Word select pin
    sd=SD_PIN,                             # Serial data pin
    mode=I2S.TX,                           # Mode: Transmit
    bits=BITS_PER_SAMPLE,                  # Bit depth
    format=I2S.MONO,                       # Stereo or Mono output
    rate=SAMPLE_RATE,                      # Sampling rate
    ibuf=BUFFER_LENGTH * 4)                # Internal buffer length (in bytes)

# --- Sine Wave Generation ---
# Create a sine wave array to be played.
# The `bytes_per_sample` is calculated based on the bit depth.
# The amplitude is set to 32767 for a full 16-bit range.
# We're generating a single sine wave cycle that will be looped.
bytes_per_sample = BITS_PER_SAMPLE // 8
samples = array.array("h", [0] * BUFFER_LENGTH) # "h" is for signed 16-bit short
amplitude = 2**15 - 1
for i in range(BUFFER_LENGTH):
    value = int(amplitude * math.sin(2 * math.pi * TONE_FREQUENCY * i / SAMPLE_RATE))
    samples[i] = value

# --- Control Mute Pin ---
# The MUTE pin is an output pin that controls the amplifier.
# Setting its value low will unmute the audio output.
mute_pin = Pin(MUTE_PIN, Pin.OUT)
mute_pin.value(0) # Set to logical low to unmute

# --- Main Loop to Play the Tone ---
# The code continuously writes the sine wave data to the I2S buffer.
# The `write` function handles sending the data to the audio pack.
print("Starting audio playback...")
while True:
    num_written = audio_out.write(samples)
    print(f"Wrote {num_written} bytes of audio data.")
    utime.sleep_ms(100)
