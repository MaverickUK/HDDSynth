import time
import synthio

def play_beep(mixer, pitch="medium", count=1, length="short", volume=0.15):
    """
    Plays a beep tone through an existing audiomixer.
    
    :param mixer: The audiomixer.Mixer object already initialized in main.py
    :param pitch: "high" (880Hz), "medium" (440Hz), or "low" (220Hz)
    :param count: Number of beeps (1, 2, or 3)
    :param length: "short" (0.1s), "medium" (0.3s), or "long" (0.6s)
    :param volume: Float between 0.0 and 1.0 (default 0.25)
    """
    
    # Map friendly names to frequencies
    pitches = {"high": 880, "medium": 440, "low": 220}
    # Map friendly names to durations (seconds)
    durations = {"short": 0.1, "medium": 0.3, "long": 0.6}
    
    freq = pitches.get(pitch.lower(), 440)
    duration = durations.get(length.lower(), 0.1)
    
    # Create a synthesizer tied to the mixer's sample rate
    synth = synthio.Synthesizer(sample_rate=mixer.sample_rate)
    
    # Attach synth to the first available mixer voice
    mixer.voice[0].play(synth)
    mixer.voice[0].level = volume
    
    for _ in range(count):
        # Start the note
        note = synthio.Note(frequency=freq)
        synth.press(note)
        time.sleep(duration)
        
        # Stop the note
        synth.release(note)
        
        # If there are more beeps coming, add a small gap
        if count > 1:
            time.sleep(duration * 0.5)
            
    # Clean up: stop the voice so it doesn't hiss or hang
    mixer.voice[0].stop()