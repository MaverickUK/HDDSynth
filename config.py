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
BUFFER_SIZE = 512          # Audio buffer size (must be multiple of 128)

# HDD Activity Detection
HDD_DATA_PORT = 0x1F0      # HDD data port address
HDD_STATUS_PORT = 0x1F7    # HDD status port address
ACTIVITY_THRESHOLD = 20    # Threshold for sustained activity detection
ACTIVITY_TIMEOUT_MS = 50   # Timeout for activity detection (milliseconds)

# --- Audio File Names ---
# These must match the exact filenames on your SD card
SPINUP_FILE = "hdd_spinup.wav"      # HDD spinup sound
IDLE_FILE = "hdd_idle.wav"          # HDD idle sound (looped)
ACCESS_FILE = "hdd_access.wav"      # HDD access sound

# --- ISA Bus Configuration ---
ISA_BUS_FREQ = 12_500_000  # PIO state machine frequency (12.5 MHz)

# --- Debug Settings ---
DEBUG_MODE = False          # Enable debug output
VERBOSE_LOGGING = True      # Enable verbose logging

# --- Pin Objects and Constants ---
# These are created after importing machine module
from machine import Pin, I2S

# I2S constants
I2S_STEREO = I2S.STEREO
I2S_MONO = I2S.MONO
I2S_TX = I2S.TX

def create_pin_objects():
    """Create Pin objects for hardware connections after configuration validation."""
    global SCK_PIN_OBJ, MOSI_PIN_OBJ, MISO_PIN_OBJ, CS_PIN_OBJ
    global BCK_PIN_OBJ, WS_PIN_OBJ, SD_PIN_OBJ, MUTE_PIN_OBJ
    
    # Create Pin objects for hardware connections
    SCK_PIN_OBJ = Pin(SCK_PIN, Pin.OUT)
    MOSI_PIN_OBJ = Pin(MOSI_PIN, Pin.OUT)
    MISO_PIN_OBJ = Pin(MISO_PIN, Pin.IN)
    CS_PIN_OBJ = Pin(CS_PIN, Pin.OUT)
    
    BCK_PIN_OBJ = Pin(BCK_PIN, Pin.OUT)
    WS_PIN_OBJ = Pin(WS_PIN, Pin.OUT)
    SD_PIN_OBJ = Pin(SD_PIN, Pin.OUT)
    MUTE_PIN_OBJ = Pin(MUTE_PIN, Pin.OUT)

def validate_config():
    """Validate configuration values to catch errors early."""
    # Validate GPIO pin ranges (Pico has GPIO 0-29)
    pins_to_check = [
        ADDR_PIN_BASE, IOR_PIN, IOW_PIN, SCK_PIN, MOSI_PIN, MISO_PIN, CS_PIN,
        BCK_PIN, WS_PIN, SD_PIN, MUTE_PIN
    ]
    
    for pin in pins_to_check:
        if not (0 <= pin <= 29):
            raise ValueError(f"Invalid GPIO pin number: {pin}")
    
    # Validate address pin count
    if ADDR_PIN_COUNT <= 0 or ADDR_PIN_BASE + ADDR_PIN_COUNT > 30:
        raise ValueError(f"Invalid address pin configuration: base={ADDR_PIN_BASE}, count={ADDR_PIN_COUNT}")
    
    # Validate audio settings
    if SAMPLE_RATE_HZ <= 0:
        raise ValueError(f"Invalid sample rate: {SAMPLE_RATE_HZ}")
    if BITS_PER_SAMPLE not in [8, 16, 24, 32]:
        raise ValueError(f"Invalid bit depth: {BITS_PER_SAMPLE}")
    if CHANNELS not in [1, 2]:
        raise ValueError(f"Invalid channel count: {CHANNELS}")
    if BUFFER_SIZE <= 0 or BUFFER_SIZE % 128 != 0:
        raise ValueError(f"Invalid buffer size: {BUFFER_SIZE} (must be multiple of 128)")
    
    # Validate activity detection settings
    if ACTIVITY_THRESHOLD <= 0:
        raise ValueError(f"Invalid activity threshold: {ACTIVITY_THRESHOLD}")
    if ACTIVITY_TIMEOUT_MS <= 0:
        raise ValueError(f"Invalid activity timeout: {ACTIVITY_TIMEOUT_MS}")
    
    print("Configuration validation passed")

# Initialize pin objects and validate configuration
create_pin_objects()
validate_config()
