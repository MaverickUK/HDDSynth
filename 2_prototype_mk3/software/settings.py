import board

SIMULATION_MODE = True # Simulate HDD activity
PLAY_SPINUP = True
ALWAYS_PLAY_JINGLE = False

ACCESS_HOLD_TIME_MS = 100 # How long to hold the access sample after an access is detected (in ms)

POWER_DETECTION = True # If True, use the power.py logic to detect if we have external power. If False, assume we always have power

# Power Sensing (external power detection via voltage divider)
POWER_SENSE_PIN = board.GP28        # ADC pin reading the divided external voltage
POWER_RESISTOR_TO_5V = 1000         # 1k Ohm (upper resistor in divider)
POWER_RESISTOR_TO_GND = 2000        # 2k Ohm (lower resistor in divider)
POWER_ADC_REF_VOLTAGE = 3.3         # Pico's internal reference
POWER_MAX_ADC_VALUE = 65535         # CircuitPython 16-bit scaling
POWER_VOLTAGE_THRESHOLD_EXT = 4.0   # External voltage (0V-5V) that triggers "powered" state

# HDD Activity
ACTIVITY_INPUT_PIN = board.GP26    # Optocoupler output from HDD activity signal (LOW = active)
HDD_LED_PIN = board.GP1            # External HDD activity LED

# Action Button
ACTION_BUTTON_PIN = board.GP2              # GPIO pin the action button is wired to
ACTION_BUTTON_SHORT_PRESS_MAX_S = 1.0      # Max press duration to register as a short press
ACTION_BUTTON_LONG_PRESS_S = 3.0           # Seconds the button must be held to register as a long press

# Mixer
MIXER_VOICES = 2 # If 1, swap out idle for access. If 2, play idle loop with access overlaid

# Rotary Encoder (used for volume and balance)
ENCODER_A_PIN = board.GP20       # Rotary encoder channel A
ENCODER_B_PIN = board.GP21       # Rotary encoder channel B
ENCODER_BUTTON_PIN = board.GP22  # Encoder push button (toggles volume <-> balance mode)

# Volume
VOLUME_DEFAULT = 0.5          # Starting volume (0.0 - 1.0)
VOLUME_STEP = 0.1             # Volume change per encoder detent (0.0 - 1.0)
VOLUME_PRINT = False          # Print volume changes to console

# Balance (idle vs access mix when MIXER_VOICES == 2)
BALANCE_DEFAULT = 0.5         # Starting balance (0.0 = idle only, 1.0 = access only)
BALANCE_STEP = 0.1            # Balance change per encoder detent (0.0 - 1.0)
BALANCE_PRINT = False         # Print balance changes to console

# SD Card
SDCARD_SCK_PIN = board.GP14    # SPI Clock
SDCARD_MOSI_PIN = board.GP15   # SPI MOSI
SDCARD_MISO_PIN = board.GP12   # SPI MISO
SDCARD_CS_PIN = board.GP13     # SPI Chip Select

SDCARD_MOUNT_POINT = '/sd'  # Mount point for the SD card
SDCARD_SAMPLE_DIR = f"{SDCARD_MOUNT_POINT}/samples" # Directory on SD card where sample packs are stored

# Amplifier
AMP_BCK_PIN = board.GP16       # I2S Bit Clock (BCK / SCLK)
AMP_WS_PIN = board.GP17        # I2S Word Select / LRCK
AMP_SD_PIN = board.GP18        # I2S Data (SD / DIN)

# Caching
CACHE_DIR = "/cache"

# Sample filenames
SAMPLE_SPINUP_FILE = f"{CACHE_DIR}/spinup.wav"
SAMPLE_IDLE_FILE = f"{CACHE_DIR}/idle.wav"
SAMPLE_ACCESS_FILE = f"{CACHE_DIR}/access.wav"
SAMPLE_SPINDOWN_FILE = f"{CACHE_DIR}/spindown.wav"

JINGLE_FILE = f"{SDCARD_MOUNT_POINT}/jingle.wav"

# NVM memory map (addresses + value constants)
NVM_ADDRESS_MODE = 0              # Byte 0 used to determine mode (0: USB, 1: WRITE)
NVM_MODE_USB = 0
NVM_MODE_WRITE = 1
NVM_ADDRESS_START_PACK_DESIRED = 65  # Starting byte for 'Desired' pack name
NVM_PACK_LENGTH = 64                 # Max length for pack names (in bytes)
NVM_ADDRESS_JINGLE = 129             # Byte used to indicate if jingle has been played
NVM_JINGLE_PLAYED = 1
NVM_JINGLE_NOT_PLAYED = 0
NVM_ADDRESS_VOLUME = 130             # Byte storing the last volume (0-100)
NVM_ADDRESS_BALANCE = 131            # Byte storing the last balance (0-100)

# Volume / Balance persistence
NVM_PERSIST_VOLUME_BALANCE = False # If True, volume and balance are saved to NVM
NVM_PERSIST_DEBOUNCE_S = 5.0       # Seconds of no change before a value is written to NVM

# Defaults used when SD is disabled but audio is still required
# (sample metadata used to configure the Mixer)
DEFAULT_SAMPLE_RATE = 16000
DEFAULT_CHANNEL_COUNT = 1
DEFAULT_BITS_PER_SAMPLE = 16
