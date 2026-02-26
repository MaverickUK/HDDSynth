import sys

# Allow other test scripts to be referenced
sys.path.append("/tests")

import time
import board
import digitalio
import audiobusio
import audiocore
import audiomixer  # NEW: Required for volume control

import util_volume

BCK_PIN = 16
WS_PIN = 17
SD_PIN = 18

def play_file(filename):
    print("Audio playback starting")
    
    try:        
        # Initialize I2S audio output
        audio_out = audiobusio.I2SOut(
            bit_clock=getattr(board, f"GP{BCK_PIN}"),
            word_select=getattr(board, f"GP{WS_PIN}"),
            data=getattr(board, f"GP{SD_PIN}")
        )
        
        # Load the WAV file
        wave_file = audiocore.WaveFile(open(filename, "rb"))
        
        # NEW: Initialize the Mixer
        # We match the mixer settings to the WAV file's properties
        mixer = audiomixer.Mixer(
            voice_count=1,
            sample_rate=wave_file.sample_rate,
            channel_count=wave_file.channel_count,
            bits_per_sample=wave_file.bits_per_sample,
            samples_per_buffer=512
        )
        
        # NEW: Attach the mixer to the audio output
        # We play the mixer, and the mixer plays the file
        audio_out.play(mixer)
        
        # NEW: Set the volume on the first voice (index 0)
        volume = util_volume.get_volume()
        
        mixer.voice[0].level = volume 
        print(f"Playing at volume: {volume}")
        
        # NEW: Play the wave file through the mixer
        mixer.voice[0].play(wave_file)
        
        # Wait for playback to complete
        # Note: Check if the mixer voice is playing, not just audio_out
        while mixer.voice[0].playing:
            time.sleep(0.1)
            mixer.voice[0].level = util_volume.get_volume()

        print("Playback completed!")
        audio_out.stop()
        
    except Exception as e:
        print(f"Error: {e}")

# Example usage:
# play_file("test.wav", volume=0.2) # Play at 20% volume
