import time
import random
import ustruct
import audio_mixer
from machine import Pin, I2S

# === Setup I2S ===
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

# === Load sound data ===
mixer = audio_mixer.Mixer()

hdd_idle_data = mixer.load_wav("hdd_idle.wav")
hdd_access_data = mixer.load_wav("hdd_access.wav")
kbd_click_data = mixer.load_wav("kbd_click.wav")

# === Setup initial sound states ===
hdd_idle = audio_mixer.Sound(hdd_idle_data, volume=0.3, loop=True)
mixer.add(hdd_idle)

hdd_access = None
kbd_click = None

# === Timing control ===
next_access_time = time.ticks_add(time.ticks_ms(), int(random.uniform(200, 2000)))
access_end_time = None

next_kbd_time = time.ticks_add(time.ticks_ms(), int(random.uniform(100, 1200)))

# === Output buffer ===
buf = bytearray(256)

print("Running: HDD idle/access + keyboard click simulation")

while True:
    now = time.ticks_ms()

    # === HDD ACCESS LOGIC ===
    if hdd_access is None and time.ticks_diff(now, next_access_time) >= 0:
        print("HDD access started")
        hdd_idle.stop()
        hdd_access = audio_mixer.Sound(hdd_access_data, volume=1.0, loop=True)
        mixer.add(hdd_access)
        access_end_time = time.ticks_add(now, int(random.uniform(100, 2000)))

    if hdd_access and time.ticks_diff(now, access_end_time) >= 0:
        print("HDD access ended")
        hdd_access.stop()
        hdd_access = None
        hdd_idle = audio_mixer.Sound(hdd_idle_data, volume=0.3, loop=True)
        mixer.add(hdd_idle)
        next_access_time = time.ticks_add(now, int(random.uniform(200, 2000)))

    # === KEYBOARD CLICK LOGIC ===
    if (kbd_click is None or not kbd_click.active) and time.ticks_diff(now, next_kbd_time) >= 0:
        kbd_click = audio_mixer.Sound(kbd_click_data, volume=1.0, loop=False)
        mixer.add(kbd_click)
        next_kbd_time = time.ticks_add(now, int(random.uniform(100, 1200)))

    # === MIXING + OUTPUT ===
    for i in range(len(buf) // 2):
        s = mixer.mix()
        ustruct.pack_into("<h", buf, i * 2, (s - 128) * 256)

    audio.write(buf)
