"""
Simple Audio Test Script for Raspberry Pi Pico
Tests audio playback using Pico Audio Pack with WAV files from flash memory.
"""

import time
import board
import digitalio
import audiobusio
import audiocore

# Audio pin configuration for Pico Audio Pack
BCK_PIN = 26    # I2S Bit Clock (BCK / SCLK)
WS_PIN = 27     # I2S Word Select / LRCK  
SD_PIN = 28     # I2S Data (SD / DIN)
MUTE_PIN = 22   # Mute pin (active low - False = unmuted, True = muted)

def main():
    print("Audio Test Script Starting...")
    print(f"Using pins: BCK=GP{BCK_PIN}, WS=GP{WS_PIN}, SD=GP{SD_PIN}")
    
    try:
        # Initialize mute pin (start muted)
        print("Initializing mute pin...")
        mute_pin = digitalio.DigitalInOut(getattr(board, f"GP{MUTE_PIN}"))
        mute_pin.direction = digitalio.Direction.OUTPUT
        mute_pin.value = True  # Start muted
        print("Mute pin initialized (started muted)")
        
        # Initialize I2S audio output
        print("Initializing I2S audio...")
        audio_out = audiobusio.I2SOut(
            bit_clock=getattr(board, f"GP{BCK_PIN}"),
            word_select=getattr(board, f"GP{WS_PIN}"),
            data=getattr(board, f"GP{SD_PIN}")
        )
        print("I2S audio initialized successfully")
        
        # Load the WAV file from flash memory
        print("Loading WAV file from flash memory...")
        try:
            # List available files first
            import os
            files = os.listdir('/')
            wav_files = [f for f in files if f.endswith('.wav')]
            print(f"Available WAV files: {wav_files}")
            
            if "nec_spinup_16hz_16bit.wav" not in wav_files:
                print("nec_spinup_16hz_16bit.wav not found. Available WAV files:")
                for f in wav_files:
                    print(f"  - {f}")
                return
            
            wave_file = audiocore.WaveFile(open("nec_spinup_16hz_16bit.wav", "rb"))
            print("WAV file loaded successfully")
            print(f"Audio format: {wave_file.sample_rate}Hz, {wave_file.bits_per_sample}bit, {wave_file.channel_count} channel(s)")
        except OSError as e:
            print(f"Error loading WAV file: {e}")
            print("Make sure 'hdd_spinup.wav' is in the root directory of your Pico")
            return
        
        # Unmute before playing audio
        print("Unmuting amplifier...")
        mute_pin.value = False
        print("Amplifier unmuted")
        
        # Play the audio file
        print("Playing audio file...")
        audio_out.play(wave_file)
        
        # Wait for playback to complete
        print("Waiting for playback to complete...")
        while audio_out.playing:
            time.sleep(0.1)
        
        # If WAV playback didn't work, try a simple tone test
        if not audio_out.playing:
            print("WAV playback completed. Testing with simple tone...")
            import array
            import math
            
            # Generate a simple 440Hz sine wave
            sample_rate = 22050
            frequency = 440
            duration = 2.0
            samples = int(sample_rate * duration)
            
            # Create a simple sine wave
            sine_wave = array.array("h", [0] * samples)
            for i in range(samples):
                sine_wave[i] = int(32767 * math.sin(2 * math.pi * frequency * i / sample_rate))
            
            print("Playing test tone (440Hz for 2 seconds)...")
            audio_out.play(sine_wave, sample_rate=sample_rate)
            
            # Wait for tone to complete
            while audio_out.playing:
                time.sleep(0.1)
            print("Test tone completed")
        
        print("Playback completed!")
        
        # Clean up
        print("Muting amplifier...")
        mute_pin.value = True
        audio_out.stop()
        mute_pin.deinit()
        print("Audio test completed successfully")
        
    except Exception as e:
        print(f"Error during audio test: {e}")
        import traceback
        traceback.print_exception(type(e), e, e.__traceback__)

if __name__ == "__main__":
    main()
