import time
import random
import ustruct
import audio_mixer
from machine import Pin, I2S

# === Setup I2S Audio Interface ===
# These are the GPIO pins used to connect the Pico to the I2S audio DAC or Audio Pack.
SCK = Pin(18)  # I2S clock
WS  = Pin(19)  # Word select / LR clock
SD  = Pin(20)  # Serial data out

# Configure I2S peripheral for audio output (mono, 16-bit, 22050 Hz)
audio = I2S(
    0,
    sck=SCK,
    ws=WS,
    sd=SD,
    mode=I2S.TX,
    bits=16,
    format=I2S.MONO,
    rate=22050,
    ibuf=2048
)

# === Load WAV files into memory ===
# The WAVs are loaded as bytearrays from the file system (after skipping headers).
# Make sure they are mono, 8-bit PCM, 22050 Hz WAV files.
mixer = audio_mixer.Mixer()
hdd_idle_data   = mixer.load_wav("hdd_idle.wav")
hdd_access_data = mixer.load_wav("hdd_access.wav")
kbd_click_data  = mixer.load_wav("kbd_click.wav")

# === Start playing the HDD idle sound immediately ===
# This will loop in the background unless an HDD access occurs.
hdd_idle = audio_mixer.Sound(hdd_idle_data, volume=0.3, loop=True)
mixer.add(hdd_idle)

# === State variables for sound effects ===
hdd_access = None  # Will store the current access sound if one is playing
kbd_click  = None  # Will store the keyboard click sound when triggered

# === Timers to control when sounds are triggered ===
# These use `time.ticks_ms()` to allow for millisecond-precision scheduling
next_access_time = time.ticks_add(time.ticks_ms(), int(random.uniform(200, 2000)))
access_end_time  = None  # Will be set when access starts

next_kbd_time = time.ticks_add(time.ticks_ms(), int(random.uniform(100, 1200)))

# === Audio Output Buffer ===
# I2S expects signed 16-bit values; we generate them from 8-bit mix output
buf = bytearray(256)

print("Running: HDD idle/access + keyboard click simulation")

# === Main loop ===
while True:
    now = time.ticks_ms()

    # --- HDD Access Trigger ---
    if hdd_access is None and time.ticks_diff(now, next_access_time) >= 0:
        print("HDD access started")

        # Stop the looping idle sound
        hdd_idle.stop()

        # Start the HDD access sound (looping so it can play longer than one cycle)
        hdd_access = audio_mixer.Sound(hdd_access_data, volume=1.0, loop=True)
        mixer.add(hdd_access)

        # Decide how long access should last (between 0.1s and 2s)
        access_duration = int(random.uniform(100, 2000))
        access_end_time = time.ticks_add(now, access_duration)

    # --- HDD Access End ---
    if hdd_access and time.ticks_diff(now, access_end_time) >= 0:
        print("HDD access ended")

        # Stop the HDD access sound
        hdd_access.stop()
        hdd_access = None
        access_end_time = None

        # Restart the idle sound
        hdd_idle = audio_mixer.Sound(hdd_idle_data, volume=0.3, loop=True)
        mixer.add(hdd_idle)

        # Schedule the next access event
        next_access_time = time.ticks_add(now, int(random.uniform(200, 2000)))

    # --- Keyboard Click Logic ---
    # This plays short typing sounds at random intervals, independently from HDD logic
    if (kbd_click is None or not kbd_click.active) and time.ticks_diff(now, next_kbd_time) >= 0:
        kbd_click = audio_mixer.Sound(kbd_click_data, volume=1.0, loop=False)
        mixer.add(kbd_click)

        # Schedule the next keypress event (100ms–1.2s later)
        next_kbd_time = time.ticks_add(now, int(random.uniform(100, 1200)))

    # --- Generate Audio Samples and Send to I2S ---
    # For each sample in the buffer, mix all active sounds and convert to 16-bit
    for i in range(len(buf) // 2):
        sample_8bit = mixer.mix()                     # Mix all sounds into one 8-bit sample (0–255)
        sample_16bit = (sample_8bit - 128) * 256       # Convert 8-bit unsigned -> 16-bit signed
        ustruct.pack_into("<h", buf, i * 2, sample_16bit)  # Write sample into buffer

    # Send buffer to I2S audio output
    audio.write(buf)
