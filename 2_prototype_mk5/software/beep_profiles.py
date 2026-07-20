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

# Profiles map a named event to a set of play_beep arguments.
PROFILE = {
    ### Operations ###
    "CHANGE_PACK": {
        "pitch": PITCH_HIGH,
        "count": 1,
        "length": LENGTH_SHORT,
        "wave": WAVE_TRIANGLE,
    },
    "FACTORY_RESET": {
        "pitch": PITCH_HIGH,
        "count": 1,
        "length": LENGTH_LONG,
        "wave": WAVE_TRIANGLE,
    },
    "VOLUME_MODE": {
        "pitch": PITCH_HIGH,
        "count": 2,
        "length": LENGTH_SHORT,
        "wave": WAVE_TRIANGLE,
    },
    "BALANCE_MODE": {
        "pitch": PITCH_HIGH,
        "count": 3,
        "length": LENGTH_SHORT,
        "wave": WAVE_TRIANGLE,
    },
    ### Errors ###
    "NO_SD_CARD": {
        "pitch": PITCH_LOW,
        "count": 1,
        "length": LENGTH_SHORT,
    },
    "NO_PACKS_ON_SD_CARD": {
        "pitch": PITCH_LOW,
        "count": 2,
        "length": LENGTH_SHORT,
    },
    "NOT_ENOUGH_SPACES_FOR_PACK": {
        "pitch": PITCH_LOW,
        "count": 3,
        "length": LENGTH_SHORT,
    },
    "CORRUPTED_PACK": {
        "pitch": PITCH_LOW,
        "count": 4,
        "length": LENGTH_SHORT,
    },
    "PACK_NOT_FOUND": {
        "pitch": PITCH_LOW,
        "count": 5,
        "length": LENGTH_SHORT,
    },
}
