import time
import math
import array
import synthio

import settings

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
}

# --- Internal Helpers ---

def _get_waveform(wave_type=WAVE_SIN):
    """Generates a 512-sample lookup table for the synthesizer."""
    size = 512

    if wave_type == WAVE_SIN:
        return array.array('h', [
            int(math.sin(2 * math.pi * i / size) * 32767)
            for i in range(size)
        ])

    if wave_type == WAVE_TRIANGLE:
        samples = array.array('h', [0] * size)
        for i in range(size):
            if i < size // 2:
                samples[i] = int(-32767 + (i * 65535 / (size // 2)))
            else:
                samples[i] = int(32767 - ((i - size // 2) * 65535 / (size // 2)))
        return samples

    return _get_waveform(WAVE_SIN)


def _get_envelope():
    """Returns a standard ADSR envelope to prevent clicking."""
    return synthio.Envelope(
        attack_time=0.02,
        decay_time=0.1,
        sustain_level=0.8,
        release_time=0.05,
    )

# --- Public API ---

def play_beep(mixer, pitch=PITCH_MEDIUM, count=1, length=LENGTH_SHORT, volume=0.8, wave=WAVE_SIN):
    """Plays a smooth beep tone on the dedicated beep voice."""
    waveform = _get_waveform(wave)
    envelope = _get_envelope()
    synth = synthio.Synthesizer(sample_rate=mixer.sample_rate)

    # Use the dedicated beep voice so the idle/access loops keep playing underneath.
    beep_voice = mixer.voice[settings.MIXER_VOICES]
    beep_voice.play(synth)
    beep_voice.level = volume

    for i in range(count):
        note = synthio.Note(frequency=pitch, waveform=waveform, envelope=envelope)

        synth.press(note)
        time.sleep(length)
        synth.release(note)

        # Small buffer for the envelope release to finish
        time.sleep(0.05)

        # Inter-beep gap
        if i < count - 1:
            time.sleep(length * 0.4)

    beep_voice.stop()


def play_beep_type(mixer, beep_type):
    """Looks up a beep profile by name and plays it."""
    config = PROFILE.get(beep_type.upper())

    if config is None:
        print(f"Warning: Beep type '{beep_type}' not found in beep.py")
        return

    play_beep(
        mixer,
        pitch=config.get("pitch", PITCH_MEDIUM),
        count=config.get("count", 1),
        length=config.get("length", LENGTH_SHORT),
        wave=config.get("wave", WAVE_SIN),
    )
