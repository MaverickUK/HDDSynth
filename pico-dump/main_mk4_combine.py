import machine
import os
import time
from machine import I2S
import sdcard
import rp2
from machine import Pin

# --- SD Card Configuration ---
SCK_PIN = machine.Pin(14)
MOSI_PIN = machine.Pin(15)
MISO_PIN = machine.Pin(12)
CS_PIN = machine.Pin(13)
MOUNT_POINT = '/sd'

# --- Audio Configuration ---
BCK_PIN = machine.Pin(26, machine.Pin.OUT)
WS_PIN = machine.Pin(27, machine.Pin.OUT)
SD_PIN = machine.Pin(28, machine.Pin.OUT)
MUTE_PIN = machine.Pin(22, machine.Pin.OUT)

# I2S parameters
SAMPLE_RATE_HZ = 16000
BITS_PER_SAMPLE = 16
CHANNELS = I2S.STEREO
BUFFER_SIZE = 512

# Audio file names
WAVE_FILE_SPINUP = "nec_spinup.wav"
WAVE_FILE_IDLE = "nec_idle_long.wav"
WAVE_FILE_ACCESS = "nec_access.wav"

# Global state variables for audio streaming
audio_out = None
idle_file = None
access_file = None

# --- Audio Playback Functions ---
def setup_audio_player():
    """Initializes the I2S audio output."""
    global audio_out
    if audio_out is None:
        audio_out = I2S(
            0, sck=BCK_PIN, ws=WS_PIN, sd=SD_PIN, mode=I2S.TX,
            bits=BITS_PER_SAMPLE, format=CHANNELS, rate=SAMPLE_RATE_HZ, ibuf=BUFFER_SIZE
        )

def stream_audio_chunk(file_object, is_looping):
    """
    Streams a single chunk of audio.
    Returns True if playback is active, False if file ends and not looping.
    """
    global audio_out
    if audio_out is None:
        setup_audio_player()
        MUTE_PIN.value(0)
    
    audio_data = file_object.read(BUFFER_SIZE)
    
    if not audio_data:
        if is_looping:
            file_object.seek(44)  # Go back to start of audio data
            audio_data = file_object.read(BUFFER_SIZE)
        else:
            return False
            
    audio_out.write(audio_data)
    return True

def play_full_file(filename):
    """
    Plays an entire WAV file from start to finish.
    """
    try:
        with open(MOUNT_POINT + '/' + filename, 'rb') as f:
            f.seek(44)
            setup_audio_player()
            MUTE_PIN.value(0)
            while True:
                audio_data = f.read(BUFFER_SIZE)
                if not audio_data:
                    break
                audio_out.write(audio_data)
            MUTE_PIN.value(1)
            audio_out.deinit()
            print(f"Finished playing {filename}")
    except Exception as e:
        print(f"Error playing {filename}: {e}")

# --- PIO Bus Monitor Configuration ---
ADDR_PIN_BASE = 0
ADDR_PIN_COUNT = 10
IOR_PIN = 10
IOW_PIN = 11

@rp2.asm_pio(in_shiftdir=rp2.PIO.SHIFT_LEFT, autopush=True, push_thresh=10, fifo_join=rp2.PIO.JOIN_RX)
def ior_pio_program():
    wrap_target()
    wait(0, pin, 0)
    in_(pins, 10)
    wrap()

@rp2.asm_pio(in_shiftdir=rp2.PIO.SHIFT_LEFT, autopush=True, push_thresh=10, fifo_join=rp2.PIO.JOIN_RX)
def iow_pio_program():
    wrap_target()
    wait(0, pin, 0)
    in_(pins, 10)
    wrap()

# Global variables for PIO
sm_ior = None
sm_iow = None
last_activity_time = 0
activity_threshold = 20
hdd_activity_counter = 0

def check_for_hdd_activity():
    """Checks the PIO FIFOs and returns True if HDD activity is detected."""
    global hdd_activity_counter, last_activity_time
    current_time = time.ticks_ms()

    # Reset counter if activity stops for more than 100ms
    if time.ticks_diff(current_time, last_activity_time) > 100:
        hdd_activity_counter = 0
    
    # Read all available data from the FIFOs
    while sm_ior.rx_fifo() > 0:
        addr = sm_ior.get()
        last_activity_time = current_time
        if addr == 0x1F0 or addr == 0x1F7:
            hdd_activity_counter += 1

    while sm_iow.rx_fifo() > 0:
        addr = sm_iow.get()
        last_activity_time = current_time
        if addr == 0x1F0 or addr == 0x1F7:
            hdd_activity_counter += 1
            
    return hdd_activity_counter > activity_threshold

# --- Main Program Logic ---
if __name__ == '__main__':
    print("--- HDD Synth ---")

    # --- SD Card Initialization ---
    try:
        spi = machine.SPI(1, baudrate=1000000, polarity=0, phase=0, sck=SCK_PIN, mosi=MOSI_PIN, miso=MISO_PIN)
        sd = sdcard.SDCard(spi, CS_PIN)
        os.mount(sd, MOUNT_POINT)
        print("✅ SD card mounted successfully.")
    except Exception as e:
        print(f"❌ Error mounting SD card: {e}")
        raise SystemExit

    # --- PIO State Machine Setup ---
    print("Initializing ISA bus monitor...")
    addr_pins = [Pin(i, Pin.IN, Pin.PULL_UP) for i in range(ADDR_PIN_COUNT)]
    ior_pin = Pin(IOR_PIN, Pin.IN, Pin.PULL_UP)
    iow_pin = Pin(IOW_PIN, Pin.IN, Pin.PULL_UP)
    sm_ior = rp2.StateMachine(0, ior_pio_program, freq=12_500_000, in_base=Pin(ADDR_PIN_BASE), jmp_pin=ior_pin)
    sm_iow = rp2.StateMachine(1, iow_pio_program, freq=12_500_000, in_base=Pin(ADDR_PIN_BASE), jmp_pin=iow_pin)
    sm_ior.active(1)
    sm_iow.active(1)
    print("✅ ISA bus monitor started.")
    MUTE_PIN.value(1)
    time.sleep_ms(200)

    # --- Initial Spin-up Sound ---
    print(f"Playing '{WAVE_FILE_SPINUP}'...")
    play_full_file(WAVE_FILE_SPINUP)
    
    # Open the audio files once to keep them ready
    try:
        idle_file = open(MOUNT_POINT + '/' + WAVE_FILE_IDLE, 'rb')
        access_file = open(MOUNT_POINT + '/' + WAVE_FILE_ACCESS, 'rb')
        idle_file.seek(44)
        access_file.seek(44)
    except Exception as e:
        print(f"❌ Error opening audio files: {e}")
        raise SystemExit

    # --- Main Audio Streaming and Monitoring Loop ---
    current_state = 'IDLE'
    print("Beginning audio stream...")
    
    try:
        while True:
            is_active = check_for_hdd_activity()
            
            if is_active:
                if current_state != 'ACCESS':
                    print("Transitioning to ACCESS state.")
                    current_state = 'ACCESS'
                    access_file.seek(44) # Start from the beginning of the access sound
                    if audio_out: audio_out.deinit() # Re-initialize I2S for a clean start
                    setup_audio_player()
                    MUTE_PIN.value(0)
                
                stream_audio_chunk(access_file, is_looping=True)
            else:
                if current_state != 'IDLE':
                    print("Transitioning to IDLE state.")
                    current_state = 'IDLE'
                    idle_file.seek(44) # Start from the beginning of the idle sound
                    if audio_out: audio_out.deinit()
                    setup_audio_player()
                    MUTE_PIN.value(0)

                stream_audio_chunk(idle_file, is_looping=True)

    except KeyboardInterrupt:
        print("\nScript stopped.")
    finally:
        # Clean up resources
        if audio_out: audio_out.deinit()
        sm_ior.active(0)
        sm_iow.active(0)
        idle_file.close()
        access_file.close()
        os.umount(MOUNT_POINT)
        print("ISA monitor stopped and SD card unmounted.")