import time
import random
import audio_mixer
from machine import Pin, I2S

# Setup I2S
SCK = Pin(18)
WS = Pin(19)
SD = Pin(20)

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

# Load sounds
mixer = audio_mixer.Mixer()
hdd_data = mixer.load_wav("hdd_idle.wav")
kbd_data = mixer.load_wav("kbd_click.wav")

# Create sound objects
hdd = audio_mixer.Sound(hdd_data, volume=0.5, loop=True)
kbd = None  # Not playing initially
mixer.add(hdd)

# Output buffer (16-bit samples)
buf = bytearray(256)

print("Audio mixer running...")

while True:
    # Randomly trigger keyboard sound
    if kbd is None or not kbd.active:
        if random.random() < 0.01:  # ~1% chance per loop
            kbd = audio_mixer.Sound(kbd_data, volume=1.0, loop=False)
            mixer.add(kbd)
    
    # Fill buffer
    for i in range(len(buf) // 2):
        s = mixer.mix()
        ustruct.pack_into("<h", buf, i*2, (s - 128) * 256)  # 8-bit to signed 16-bit

    # Write to I2S
    audio.write(buf)
