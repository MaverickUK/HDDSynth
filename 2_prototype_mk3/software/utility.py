import time
import audio

def active_pause(seconds, mixer):
    """Pauses for 'seconds' but keeps volume keeping active"""
    print("Activing pause for", seconds, "seconds")
    start_time = time.monotonic()


    while (time.monotonic() - start_time) < seconds:
        audio.set_volume(mixer)
        
        # Micro-sleep to keep the CPU stable and prevent USB dropouts
        time.sleep(0.01) 
