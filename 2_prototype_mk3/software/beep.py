import time
import math
import array
import synthio

# We use a dictionary to define "Profiles"
# Each profile contains the arguments for your play_beep function
PROFILE = {
    ### Operations ###
    "CHANGE_PACK": {
        "pitch": "high",
        "count": 1,
        "length": "short",
        "wave": "triangle"
    },    
    "FACTORY_RESET": {
        "pitch": "high",
        "count": 1,
        "length": "long",
        "wave": "triangle"
    },  
    ### Errors ###
    "NO_SD_CARD": {
        "pitch": "low",
        "count": 1,
        "length": "short"
    },
    "NO_PACKS_ON_SD_CARD": {
        "pitch": "low",
        "count": 2,
        "length": "short"
    },
    "NOT_ENOUGH_SPACES_FOR_PACK": {
        "pitch": "low",
        "count": 3,
        "length": "short"
    },
    "CORRUPTED_PACK": {
        "pitch": "low",
        "count": 34,
        "length": "short"
    }    
}

# --- Internal Helper Methods ---

def _get_waveform(wave_type="sin"):
    """Generates a 512-sample lookup table for the synthesizer."""
    size = 512
    debug_name = wave_type.lower()
    
    if debug_name == "sin":
        # Smooth mathematical curve
        return array.array('h', [
            int(math.sin(2 * math.pi * i / size) * 32767) 
            for i in range(size)
        ])
    
    elif debug_name == "triangle":
        # Linear ramp up and down
        samples = array.array('h', [0] * size)
        for i in range(size):
            if i < size // 2:
                samples[i] = int(-32767 + (i * 65535 / (size // 2)))
            else:
                samples[i] = int(32767 - ((i - size // 2) * 65535 / (size // 2)))
        return samples
    
    # Default to a basic Sine if type is unknown
    return _get_waveform("sin")

def _get_envelope():
    """Returns a standard ADSR envelope to prevent clicking."""
    return synthio.Envelope(
        attack_time=0.02, 
        decay_time=0.1, 
        sustain_level=0.8, 
        release_time=0.05
    )

# --- Public API ---

def play_beep(mixer, pitch="medium", count=1, length="short", volume=0.8, wave="sin"):
    """
    Plays a smooth beep tone.
    :param wave: "sin" (pure/soft) or "triangle" (audible/clear)
    """
    # 1. Map Configuration
    pitches = {"high": 1200, "medium": 440, "low": 400}
    durations = {"short": 0.1, "medium": 0.8, "long": 1}
    
    freq = pitches.get(pitch.lower(), 440)
    duration = durations.get(length.lower(), 0.1)
    
    # 2. Prepare Synth
    waveform = _get_waveform(wave)
    envelope = _get_envelope()
    synth = synthio.Synthesizer(sample_rate=mixer.sample_rate)
    
    mixer.voice[0].play(synth)
    mixer.voice[0].level = volume
    
    # 3. Play Sequence
    for i in range(count):
        note = synthio.Note(frequency=freq, waveform=waveform, envelope=envelope)
        
        synth.press(note)
        time.sleep(duration)
        synth.release(note)
        
        # Small buffer for the envelope release to finish
        time.sleep(0.05)
        
        # Inter-beep gap
        if i < count - 1:
            time.sleep(duration * 0.4)
            
    mixer.voice[0].stop()

def play_beep_type(mixer, beep_type):
    """
    Looks up a beep profile by name and plays it.
    :param beep_type: A string key from sounds.BEEPS (e.g., "NO_SD_CARD")
    """
    # 1. Get the settings from our constants file
    # Use .get() to avoid crashing if a typo happens
    config = PROFILE.get(beep_type.upper())
    
    if config:
        # 2. Call the original play_beep function
        # We use **config to "unpack" the dictionary into arguments automatically
        play_beep(
            mixer, 
            pitch=config.get("pitch", "medium"),
            count=config.get("count", 1),
            length=config.get("length", "short"),
            wave=config.get("wave", "sin")
        )
    else:
        print(f"Warning: Beep type '{beep_type}' not found in sounds.py")