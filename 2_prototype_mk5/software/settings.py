import board

SIMULATION_MODE = True # Simulate HDD activity
PLAY_SPINUP = True
PLAY_SPINDOWN = True
PLAY_IDLE = True
ALWAYS_PLAY_JINGLE = False

ACCESS_HOLD_TIME_MS = 100 # How long to hold the access sample after an access is detected (in ms)

POWER_DETECTION = True # If True, use the power.py logic to detect if we have external power. If False, assume we always have power

# Power Sensing (external power detection via voltage divider)
POWER_SENSE_PIN = board.GP28        # ADC pin reading the divided external voltage
POWER_RESISTOR_TO_5V = 10000        # 10k Ohm (upper resistor in divider)
POWER_RESISTOR_TO_GND = 10000       # 10k Ohm (lower resistor in divider)
POWER_ADC_REF_VOLTAGE = 3.3         # Pico's internal reference
POWER_MAX_ADC_VALUE = 65535         # CircuitPython 16-bit scaling
POWER_VOLTAGE_THRESHOLD_EXT = 4.0   # External voltage (0V-5V) that triggers "powered" state

# HDD Activity
ACTIVITY_INPUT_PIN = board.GP18    # Optocoupler output from HDD activity signal (LOW = active)
HDD_LED_PIN = board.GP17            # External HDD activity LED

# RGB status LED (XL-3528RGBW-HM, LCSC C2843813)
# Common anode: the shared pin sits at +3V3 and each colour's cathode is driven
# by a GPIO, so driving a pin LOW turns that channel ON (PWM duty is inverted).
# Per-channel series resistors (R19 270R red, R18 56R green, R20 33R blue) already
# balance the channel brightness, so equal duty cycles give a roughly neutral mix.
RGB_LED_RED_PIN = board.GP4
RGB_LED_GREEN_PIN = board.GP5
RGB_LED_BLUE_PIN = board.GP6
RGB_LED_PWM_FREQUENCY = 1000   # Hz — well above flicker, well below audio pickup concerns
RGB_LED_STARTUP_TEST_S = 1.0   # Duration of the power-on hue sweep (0 to disable)
RGB_LED_STARTUP_TEST_STEPS = 60

# HDD activity indication on the RGB status LED
ACTIVITY_LED_ENABLED = True         # False turns the activity indication off entirely
ACTIVITY_LED_COLOUR = (0, 255, 0)   # (R, G, B) 0-255 shown while the HDD is being accessed

# Status colours. Error and operation flashes are driven in time with the matching
# beep profile (see beep_profiles.py), so the LED and the buzzer tell the same story.
RGB_LED_ERROR_COLOUR = (255, 0, 0)       # Error beep profiles
RGB_LED_OPERATION_COLOUR = (0, 0, 255)   # Operational change beep profiles
RGB_LED_BUSY_COLOUR = (255, 255, 0)      # Internal activity before normal operation begins
RGB_LED_ERROR_REPEAT_S = 4.0             # Gap before a latched error pattern repeats
RGB_LED_BUSY_FLASH_S = 0.25              # Half-period of the busy flash

# Master brightness (0.0 - 1.0) scaling every colour the status LED shows.
RGB_LED_BRIGHTNESS = 0.5

# Action Button
ACTION_BUTTON_PIN = board.GP19              # GPIO pin the action button is wired to
ACTION_BUTTON_SHORT_PRESS_MAX_S = 1.0      # Max press duration to register as a short press
ACTION_BUTTON_LONG_PRESS_S = 3.0           # Seconds the button must be held to register as a long press

# Mixer
MIXER_VOICES = 2 # If 1, swap out idle for access. If 2, play idle loop with access overlaid

# Rotary Encoder (used for volume and balance)
ENCODER_A_PIN = board.GP20       # Rotary encoder channel A
ENCODER_B_PIN = board.GP21       # Rotary encoder channel B
ENCODER_BUTTON_PIN = board.GP22  # Encoder push button (toggles volume <-> balance mode)

# OLED display (I2C)
OLED_SDA_PIN = board.GP24        # I2C SDA (data)
OLED_SCL_PIN = board.GP25        # I2C SCL (clock)

# Volume
VOLUME_DEFAULT = 0.5          # Starting volume (0.0 - 1.0)
VOLUME_STEP = 0.05             # Volume change per encoder detent (0.0 - 1.0)
VOLUME_PRINT = False          # Print volume changes to console

# Balance (idle vs access mix when MIXER_VOICES == 2)
BALANCE_DEFAULT = 0.5         # Starting balance (0.0 = idle only, 1.0 = access only)
BALANCE_STEP = 0.1            # Balance change per encoder detent (0.0 - 1.0)
BALANCE_PRINT = False         # Print balance changes to console

# SD Card
SDCARD_REQUIRED = False         # If True, device won't run without SD card. If False, device can run without SD (if sample pack is installed)
SDCARD_CACHE_SAMPLES = False     # If True, sample packs are copied from SD to Pico flash before playback (faster, SD removable after boot).
                                # If False, samples stream directly from SD card (no caching step, SD must remain inserted).
SDCARD_BAUDRATE = 25_000_000    # SPI clock speed: 400_000 (init/safe), 8_000_000 (conservative), 12_500_000 (balanced), 25_000_000 (max)
SDCARD_SCK_PIN = board.GP10    # SPI Clock
SDCARD_MOSI_PIN = board.GP11   # SPI MOSI
SDCARD_MISO_PIN = board.GP8    # SPI MISO
SDCARD_CS_PIN = board.GP9      # SPI Chip Select

SDCARD_MOUNT_POINT = '/sd'  # Mount point for the SD card
SDCARD_SAMPLE_DIR = f"{SDCARD_MOUNT_POINT}/samples" # Directory on SD card where sample packs are stored

# Amplifier
AMP_BCK_PIN = board.GP13       # I2S Bit Clock (BCK / BLCK)
AMP_WS_PIN = board.GP14        # I2S Word Select / LRCL
AMP_SD_PIN = board.GP12        # I2S Data (SD / DIN)
AMP_SDMODE_PIN = board.GP15    # Amplifier mode pin
AMP_POWER_CONTROL = True        # If True, control amplifier power via SDMODE pin (turn on at startup, off after spindown)

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

# GPIO Safety (pull-down unused pins at boot to prevent CMOS latchup)
PULL_DOWN_UNUSED_GPIOS = True
USED_GPIO_PINS = (
    board.GP0,        # safety pin (boot.py)
    board.LED,        # onboard LED
    HDD_LED_PIN,
    RGB_LED_RED_PIN,
    RGB_LED_GREEN_PIN,
    RGB_LED_BLUE_PIN,
    ACTION_BUTTON_PIN,
    ACTIVITY_INPUT_PIN,
    POWER_SENSE_PIN,
    ENCODER_A_PIN,
    ENCODER_B_PIN,
    ENCODER_BUTTON_PIN,
    SDCARD_SCK_PIN,
    SDCARD_MOSI_PIN,
    SDCARD_MISO_PIN,
    SDCARD_CS_PIN,
    AMP_BCK_PIN,
    AMP_WS_PIN,
    AMP_SD_PIN,
    AMP_SDMODE_PIN,
    OLED_SDA_PIN,
    OLED_SCL_PIN,
)

# Defaults used when SD is disabled but audio is still required
# (sample metadata used to configure the Mixer)
DEFAULT_SAMPLE_RATE = 16000
DEFAULT_CHANNEL_COUNT = 1
DEFAULT_BITS_PER_SAMPLE = 16
