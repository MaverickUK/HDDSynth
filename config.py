# config.py
# Configuration file for HDD Synth
# Modify these settings to match your hardware setup

# --- Hardware Configuration ---
# ISA Bus Monitoring Pins
ADDR_PIN_BASE = 0          # First GPIO pin for address bus (A0)
ADDR_PIN_COUNT = 10        # Number of address pins to monitor (A0-A9)
IOR_PIN = 10               # GPIO pin for ISA IOR signal
IOW_PIN = 11               # GPIO pin for ISA IOW signal

# SD Card Pins (SPI)
SCK_PIN = 14               # SPI Clock
MOSI_PIN = 15              # SPI MOSI
MISO_PIN = 12              # SPI MISO
CS_PIN = 13                # SPI Chip Select
MOUNT_POINT = '/sd'        # SD card mount point

# Audio Pins (Pico Audio Pack)
BCK_PIN = 26               # Bit Clock (SCK)
WS_PIN = 27                # Word Select (WS)
SD_PIN = 28                # Serial Data (SD)
MUTE_PIN = 22              # Mute pin for amplifier (active low)

# --- Audio Configuration ---
SAMPLE_RATE_HZ = 16000     # Audio sample rate
BITS_PER_SAMPLE = 16       # Audio bit depth
CHANNELS = 1               # 1 = Mono, 2 = Stereo

# HDD Activity Detection
HDD_DATA_PORT = 0x1F0      # HDD data port address
HDD_STATUS_PORT = 0x1F7    # HDD status port address
ACTIVITY_THRESHOLD = 20    # Threshold for sustained activity detection (like main_mk3_debounce.py)
ACTIVITY_TIMEOUT_MS = 50   # Timeout for activity detection (milliseconds) - reset counters if no activity

# --- Audio File Names ---
# These must match the exact filenames on your SD card
SPINUP_FILE = "nec_spinup.wav"      # HDD spinup sound
IDLE_FILE = "nec_idle_long.wav"     # HDD idle sound (looped) - using the longer version
ACCESS_FILE = "nec_access.wav"      # HDD access sound

# --- ISA Bus Configuration ---
ISA_BUS_FREQ = 12_500_000  # PIO state machine frequency (12.5 MHz)
ADDRESS_BITMASK = 0xFF      # Bitmask for address comparison (lower 8 bits)

# --- Debug Settings ---
SIMULATION_MODE = True      # Simulate HDD activity for testing (like CircuitPython PoC)
VERBOSE_ACTIVITY_LOGGING = False  # Enable verbose logging of individual HDD activity events
USE_FLASH_STORAGE = True    # Use audio files stored on Pico flash memory instead of SD card

# --- Simulation and Timing Configuration ---
HDD_STATE_CHANGE_DELAY_MS = 50      # Delay for HDD state changes (milliseconds)
MAIN_LOOP_DELAY_MS = 1              # Main loop delay (milliseconds)
SPINUP_PLAYBACK_DELAY_MS = 100      # Delay for spinup audio playback loop (milliseconds)
SIMULATION_ACTIVITY_PROBABILITY = 0.7  # Probability of HDD activity in simulation (0.0-1.0)
SIMULATION_INTERVAL_MS = 5000       # Simulation interval (milliseconds)

# --- Pin Objects and Constants ---
# Pin objects are created in the main program using digitalio.DigitalInOut

def validate_config():
    """Validate configuration values to catch errors early."""
    # Validate GPIO pin ranges (Pico has GPIO 0-29)
    pins_to_check = [
        ADDR_PIN_BASE, IOR_PIN, IOW_PIN, SCK_PIN, MOSI_PIN, MISO_PIN, CS_PIN,
        BCK_PIN, WS_PIN, SD_PIN, MUTE_PIN
    ]
    
    for pin in pins_to_check:
        if not (0 <= pin <= 29):
            print(f"Warning: Invalid GPIO pin number: {pin}")
    
    # Validate address pin count
    if ADDR_PIN_COUNT <= 0 or ADDR_PIN_BASE + ADDR_PIN_COUNT > 30:
        print(f"Warning: Invalid address pin configuration: base={ADDR_PIN_BASE}, count={ADDR_PIN_COUNT}")
    
    # Validate audio settings
    if SAMPLE_RATE_HZ <= 0:
        print(f"Warning: Invalid sample rate: {SAMPLE_RATE_HZ}")
    if BITS_PER_SAMPLE not in [8, 16, 24, 32]:
        print(f"Warning: Invalid bit depth: {BITS_PER_SAMPLE}")
    if CHANNELS not in [1, 2]:
        print(f"Warning: Invalid channel count: {CHANNELS}")
    
    # Validate activity detection settings
    if ACTIVITY_THRESHOLD <= 0:
        print(f"Warning: Invalid activity threshold: {ACTIVITY_THRESHOLD}")
    if ACTIVITY_TIMEOUT_MS <= 0:
        print(f"Warning: Invalid activity timeout: {ACTIVITY_TIMEOUT_MS}")
    
    # Validate debug settings
    if not isinstance(SIMULATION_MODE, bool):
        print(f"Warning: SIMULATION_MODE should be boolean, got: {type(SIMULATION_MODE)}")
    if not isinstance(VERBOSE_ACTIVITY_LOGGING, bool):
        print(f"Warning: VERBOSE_ACTIVITY_LOGGING should be boolean, got: {type(VERBOSE_ACTIVITY_LOGGING)}")
    if not isinstance(USE_FLASH_STORAGE, bool):
        print(f"Warning: USE_FLASH_STORAGE should be boolean, got: {type(USE_FLASH_STORAGE)}")
    
    print("Configuration validation passed")

# Note: Configuration validation is called from main program
