# hdd_synth.py
# HDD Synth project: Pi Pico + ISA bus + SD card + Audio Pack
# Plays mechanical HDD audio samples depending on ISA HDD activity

import machine
import os
import time
import rp2
import sdcard
from machine import I2S, Pin

# --------------------------
# SD Card Setup
# --------------------------
SCK_PIN = machine.Pin(14)
MOSI_PIN = machine.Pin(15)
MISO_PIN = machine.Pin(12)
CS_PIN = machine.Pin(13)
MOUNT_POINT = "/sd"

# --------------------------
# Audio Setup
# --------------------------
BCK_PIN = machine.Pin(26)  # Bit Clock
WS_PIN = machine.Pin(27)   # Word Select
SD_PIN = machine.Pin(28)   # Serial Data
MUTE_PIN = machine.Pin(22, machine.Pin.OUT)

SAMPLE_RATE_HZ = 16000
BITS_PER_SAMPLE = 16
CHANNELS = I2S.STEREO
BUFFER_SIZE = 512

# --------------------------
# ISA Setup
# --------------------------
ADDR_PIN_BASE = 0
ADDR_PIN_COUNT = 10
IOR_PIN = 10
IOW_PIN = 11

# --------------------------
# PIO Programs
# --------------------------
@rp2.asm_pio(
    in_shiftdir=rp2.PIO.SHIFT_LEFT,
    autopush=True,
    push_thresh=10,
    fifo_join=rp2.PIO.JOIN_RX
)
def ior_pio_program():
    wrap_target()
    wait(0, pin, 0)
    in_(pins, 10)
    wrap()

@rp2.asm_pio(
    in_shiftdir=rp2.PIO.SHIFT_LEFT,
    autopush=True,
    push_thresh=10,
    fifo_join=rp2.PIO.JOIN_RX
)
def iow_pio_program():
    wrap_target()
    wait(0, pin, 0)
    in_(pins, 10)
    wrap()

# --------------------------
# Globals
# --------------------------
i2s = None
sm_ior = None
sm_iow = None

# --------------------------
# Init Functions
# --------------------------
def init_sd():
    print("📀 Mounting SD card...")
    spi = machine.SPI(1, baudrate=1_000_000,
                      polarity=0, phase=0,
                      sck=SCK_PIN, mosi=MOSI_PIN, miso=MISO_PIN)
    sd = sdcard.SDCard(spi, CS_PIN)
    os.mount(sd, MOUNT_POINT)
    print("✅ SD mounted at", MOUNT_POINT)
    return True

def init_audio():
    global i2s
    print("🔊 Initializing I2S audio...")
    i2s = I2S(0,
              sck=BCK_PIN,
              ws=WS_PIN,
              sd=SD_PIN,
              mode=I2S.TX,
              bits=BITS_PER_SAMPLE,
              format=CHANNELS,
              rate=SAMPLE_RATE_HZ,
              ibuf=BUFFER_SIZE)
    MUTE_PIN.value(1)  # keep muted initially
    print("✅ I2S ready")

def find_free_sms(count=2):
    """Return a list of free StateMachine indices (length = count)."""
    free = []
    for i in range(8):  # RP2040 has 8 SMs total
        try:
            sm = rp2.StateMachine(i)  # try to grab
            sm.deinit()               # free if possible
            free.append(i)
        except Exception:
            # In use by another driver (like I2S), skip
            pass
    if len(free) < count:
        raise RuntimeError("Not enough free StateMachines available")
    return free[:count]

def init_isa():
    global sm_ior, sm_iow
    print("🖥️ Initializing ISA monitor...")

    # Pick two free SMs dynamically
    sm_indexes = find_free_sms(2)
    ior_index, iow_index = sm_indexes
    print(f"ℹ️ Using SM{ior_index} for IOR, SM{iow_index} for IOW")

    # Address pins as input
    _ = [Pin(i, Pin.IN, Pin.PULL_UP) for i in range(ADDR_PIN_COUNT)]
    ior_pin = Pin(IOR_PIN, Pin.IN, Pin.PULL_UP)
    iow_pin = Pin(IOW_PIN, Pin.IN, Pin.PULL_UP)

    sm_ior = rp2.StateMachine(
        ior_index, ior_pio_program, freq=12_500_000,
        in_base=Pin(ADDR_PIN_BASE), jmp_pin=ior_pin
    )
    sm_iow = rp2.StateMachine(
        iow_index, iow_pio_program, freq=12_500_000,
        in_base=Pin(ADDR_PIN_BASE), jmp_pin=iow_pin
    )

    sm_ior.active(1)
    sm_iow.active(1)
    print("✅ ISA state machines active")


# --------------------------
# Audio Helpers
# --------------------------
def play_wav(filename, loop=False):
    """
    Plays a WAV file from the SD card via I2S.
    """
    full_path = MOUNT_POINT + "/" + filename
    print(f"▶️ Playing {filename} (loop={loop})")

    try:
        with open(full_path, "rb") as f:
            header = f.read(44)  # skip WAV header
            MUTE_PIN.value(0)   # unmute amp

            while True:
                data = f.read(BUFFER_SIZE)
                if not data:
                    if loop:
                        f.seek(44)  # rewind to after header
                        continue
                    else:
                        break
                i2s.write(data)
    except Exception as e:
        print("💥 Error playing audio:", e)
    finally:
        MUTE_PIN.value(1)  # mute amp
        print("⏹️ Playback finished")

# --------------------------
# Main
# --------------------------
def main():
    print("🚀 HDD Synth starting...")

    init_sd()
    init_audio()
    init_isa()

    # Play spinup once
    play_wav("NEC_spinup.wav", loop=False)

    # Then idle loop forever
    while True:
        play_wav("NEC_idle_long.wav", loop=True)

# --------------------------
# Run with crash handler
# --------------------------
try:
    main()
except Exception as e:
    import sys
    sys.print_exception(e)
    print("💥 Crash in main:", e)
