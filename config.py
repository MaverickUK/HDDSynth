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
BUFFER_SIZE = 1024         # Audio buffer size (must be multiple of 128)

# HDD Activity Detection
HDD_DATA_PORT = 0x1F0      # HDD data port address
HDD_STATUS_PORT = 0x1F7    # HDD status port address
ACTIVITY_THRESHOLD = 20    # Threshold for sustained activity detection
ACTIVITY_TIMEOUT_MS = 200   # Timeout for activity detection (milliseconds)

# --- Audio File Names ---
# These must match the exact filenames on your SD card
SPINUP_FILE = "nec_spinup.wav"      # HDD spinup sound
IDLE_FILE = "nec_idle_long.wav"     # HDD idle sound (looped) - using the longer version
ACCESS_FILE = "nec_access.wav"      # HDD access sound

# --- ISA Bus Configuration ---
ISA_BUS_FREQ = 12_500_000  # PIO state machine frequency (12.5 MHz)

# --- Debug Settings ---
DEBUG_MODE = False          # Enable debug output
VERBOSE_LOGGING = True      # Enable verbose logging
SIMULATION_MODE = True      # Simulate HDD activity for testing (like CircuitPython PoC)

# --- Simulation and Timing Configuration ---
HDD_STATE_CHANGE_DELAY_MS = 50      # Delay for HDD state changes (milliseconds)
MAIN_LOOP_DELAY_MS = 1              # Main loop delay (milliseconds)
SPINUP_PLAYBACK_DELAY_MS = 100      # Delay for spinup audio playback loop (milliseconds)
SIMULATION_ACTIVITY_PROBABILITY = 0.7  # Probability of HDD activity in simulation (0.0-1.0)
SIMULATION_INTERVAL_MS = 5000       # Simulation interval (milliseconds)

# --- Pin Objects and Constants ---
# These are created after importing machine module
# Note: I2S constants will be set when machine module is available

def create_pin_objects():
    """Create Pin objects for hardware connections after configuration validation."""
    # Note: This function requires machine.Pin to be available
    # It should be called from the main program after imports
    pass

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
    if BUFFER_SIZE <= 0 or BUFFER_SIZE % 128 != 0:
        print(f"Warning: Invalid buffer size: {BUFFER_SIZE} (must be multiple of 128)")
    
    # Validate activity detection settings
    if ACTIVITY_THRESHOLD <= 0:
        print(f"Warning: Invalid activity threshold: {ACTIVITY_THRESHOLD}")
    if ACTIVITY_TIMEOUT_MS <= 0:
        print(f"Warning: Invalid activity timeout: {ACTIVITY_TIMEOUT_MS}")
    
    print("Configuration validation passed")

# Note: Pin objects and configuration validation should be called from main program
