
# --- Audio Configuration ---
WAVE_FILE = "nec_spinup_16hz_16bit.wav"



# audio_player.py
#
# A MicroPython script for the Raspberry Pi Pico to play a WAV file
# through a Pico Audio Pack using the I2S protocol.
#
# This script is designed for a 16-bit, 44.1kHz, stereo WAV file.
# You must upload your WAV file to the Pico with the name 'audio.wav'.

import machine
import os
import time
from machine import I2S

# --- Pin Definitions ---
# The pins for the I2S connection as requested.
BCK_PIN = machine.Pin(26, machine.Pin.OUT) # Bit Clock (SCK)
WS_PIN = machine.Pin(27, machine.Pin.OUT)  # Word Select (WS)
SD_PIN = machine.Pin(28, machine.Pin.OUT)  # Serial Data (SD)

# Mute pin for the amplifier, active low.
MUTE_PIN = machine.Pin(22, machine.Pin.OUT)

# --- Configuration Constants ---
# Common I2S configuration parameters.
# You can change these to match your WAV file's format.
SAMPLE_RATE_HZ = 16000
BITS_PER_SAMPLE = 16
CHANNELS = I2S.STEREO # Use I2S.MONO if your audio is mono

# A buffer for reading and writing audio data.
# Larger buffers can improve performance but use more memory.
# It is recommended to use a multiple of 128.
BUFFER_SIZE = 512

def play_audio(filename=WAVE_FILE):
    """
    Plays a WAV file from the flash memory of the Pi Pico.
    The script will check if the file exists and unmute the amplifier
    before playback.
    """
    print("Initializing audio playback...")

    try:
        if filename not in os.listdir():
            print(f"Error: The file '{filename}' was not found on the Pico.")
            return

        with open(filename, 'rb') as audio_file:
            # Skip the WAV header (first 44 bytes).
            # This script assumes a standard WAV format with a 44-byte header.
            header = audio_file.read(44)
            print("WAV header skipped.")

            # Create the I2S audio output object.
            audio_out = I2S(
                0,                          # I2S bus number (0 or 1 on RP2040)
                sck=BCK_PIN,
                ws=WS_PIN,
                sd=SD_PIN,
                mode=I2S.TX,                # Transmit mode
                bits=BITS_PER_SAMPLE,       # 16-bit data
                format=CHANNELS,            # Stereo or mono
                rate=SAMPLE_RATE_HZ,        # Audio sample rate
                ibuf=BUFFER_SIZE            # Internal buffer size
            )

            # Unmute the amplifier by setting the MUTE_PIN low.
            MUTE_PIN.value(0)
            print("Amplifier unmuted.")

            # Read the audio data in chunks and write to the I2S output.
            num_bytes_written = 0
            # Read all remaining data
            while True:
                audio_data = audio_file.read(BUFFER_SIZE)
                if not audio_data:
                    break
                num_bytes_written += audio_out.write(audio_data)

            # Mute the amplifier again to save power and prevent noise.
            MUTE_PIN.value(1)
            print("Amplifier muted.")

            # Close the I2S object and release the pins.
            audio_out.deinit()
            print("Audio playback finished.")

    except Exception as e:
        print(f"An error occurred: {e}")

# --- Main execution ---
if __name__ == '__main__':
    # Initially mute the amplifier to prevent pop noise on startup.
    MUTE_PIN.value(1)
    
    # Wait a moment before starting playback.
    time.sleep(1) 
    
    # Call the main function to play the audio.
    play_audio()

    print("Script execution complete.")
