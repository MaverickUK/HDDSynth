# --- Pitch (Hz) ---
PITCH_HIGH = 1200
PITCH_MEDIUM = 440
PITCH_LOW = 400

# --- Length (seconds per beep) ---
LENGTH_SHORT = 0.1
LENGTH_MEDIUM = 0.8
LENGTH_LONG = 1.0

# --- Waveform ---
WAVE_SIN = "sin"
WAVE_TRIANGLE = "triangle"

# --- Categories ---
# Chooses the RGB status LED colour that flashes in time with the beeps.
# Errors additionally latch, so the LED keeps repeating the pattern.
CATEGORY_OPERATION = "operation"
CATEGORY_ERROR = "error"

# Profiles map a named event to a set of play_beep arguments.
PROFILE = {
    ### Operations ###
    "CHANGE_PACK": {
        "pitch": PITCH_HIGH,
        "count": 1,
        "length": LENGTH_SHORT,
        "wave": WAVE_TRIANGLE,
        "category": CATEGORY_OPERATION,
    },
    "FACTORY_RESET": {
        "pitch": PITCH_HIGH,
        "count": 1,
        "length": LENGTH_LONG,
        "wave": WAVE_TRIANGLE,
        "category": CATEGORY_OPERATION,
    },
    "VOLUME_MODE": {
        "pitch": PITCH_HIGH,
        "count": 2,
        "length": LENGTH_SHORT,
        "wave": WAVE_TRIANGLE,
        "category": CATEGORY_OPERATION,
    },
    "BALANCE_MODE": {
        "pitch": PITCH_HIGH,
        "count": 3,
        "length": LENGTH_SHORT,
        "wave": WAVE_TRIANGLE,
        "category": CATEGORY_OPERATION,
    },
    ### Errors ###
    "NO_SD_CARD": {
        "pitch": PITCH_LOW,
        "count": 1,
        "length": LENGTH_SHORT,
        "category": CATEGORY_ERROR,
    },
    "NO_PACKS_ON_SD_CARD": {
        "pitch": PITCH_LOW,
        "count": 2,
        "length": LENGTH_SHORT,
        "category": CATEGORY_ERROR,
    },
    "NOT_ENOUGH_SPACES_FOR_PACK": {
        "pitch": PITCH_LOW,
        "count": 3,
        "length": LENGTH_SHORT,
        "category": CATEGORY_ERROR,
    },
    "CORRUPTED_PACK": {
        "pitch": PITCH_LOW,
        "count": 4,
        "length": LENGTH_SHORT,
        "category": CATEGORY_ERROR,
    },
    "PACK_NOT_FOUND": {
        "pitch": PITCH_LOW,
        "count": 5,
        "length": LENGTH_SHORT,
        "category": CATEGORY_ERROR,
    },
}
