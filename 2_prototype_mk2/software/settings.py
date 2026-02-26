
import board

SIMULATION_MODE = True # Simulate HDD activity
PLAY_SPINUP = True
PLAY_JINGLE = False

# Volume
POT_PIN = board.GP27  # Potentiometer connected to GP27 (ADC1)
VOLUME_DISCRETE = True # Round volume to discrete levels
VOLUME_DISCRETE_RANGE = 50 # Number of possible volume levels
VOLUME_PRINT = False # Print volume changes to console

# Mixer
MIXER_VOICES = 2 # If 1, swap out idle for access. If 2, play idle loop with access overlaid
RANDOM_ACCESS_START = True # Start access sample in random position to reduce repetitiveness

# SD Card
SDCARD_SCK_PIN = 14    # SPI Clock
SDCARD_MOSI_PIN = 15   # SPI MOSI  
SDCARD_MISO_PIN = 12   # SPI MISO
SDCARD_CS_PIN = 13     # SPI Chip Select

# Amplifier
AMP_BCK_PIN = board.GP16       # I2S Bit Clock (BCK / SCLK)
AMP_WS_PIN = board.GP17        # I2S Word Select / LRCK  
AMP_SD_PIN = board.GP18        # I2S Data (SD / DIN)

SDCARD_MOUNT_POINT = '/sd'  # Mount point for the SD card
SDCARD_SAMPLE_DIR = f"{SDCARD_MOUNT_POINT}/samples" # Directory on SD card where sample packs are stored

# Default sample filenames
SAMPLE_SPINUP_FILE = "cache/spinup.wav" # TODO - reference CACHE_DIR
SAMPLE_IDLE_FILE = "cache/idle.wav"
SAMPLE_ACCESS_FILE = "cache/access.wav"

JINGLE_FILE = "sd/HDDSynthJingle_16hz_16bit.wav"

# Caching
CACHE_DIR = "/cache"

# NVM memory map
NVM_ADDRESS_MODE = 0 # Byte 0 used to determine mode (0: USB, 1: WRITE)
NVM_ADDRESS_START_PACK_CURRENT = 1 # Starting byte for 'Current' pack name (No longer used)
NVM_ADDRESS_START_PACK_DESIRED = 65 # Starting byte for 'Desired' pack name
NVM_PACK_LENGTH = 64 # Max length for pack names (in bytes)

# Defaults used when SD is disabled but audio is still required
# (sample metadata used to configure the Mixer)
DEFAULT_SAMPLE_RATE = 16000
DEFAULT_CHANNEL_COUNT = 1
DEFAULT_BITS_PER_SAMPLE = 16