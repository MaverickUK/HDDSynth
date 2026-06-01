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
BCK_PIN = 16 #26#10 #26    # I2S Bit Clock (BCK / SCLK)
WS_PIN = 17 #27#11 #27     # I2S Word Select / LRCK  
SD_PIN = 18 #28#9 #28     # I2S Data (SD / DIN)
# MUTE_PIN = 22   # Mute pin (active low - False = unmuted, True = muted)

def main():
    print("Audio Test Script Starting...")
    print(f"Using pins: BCK=GP{BCK_PIN}, WS=GP{WS_PIN}, SD=GP{SD_PIN}")
    
    try:
        # Initialize mute pin (start muted)
        #print("Initializing mute pin...")
        #mute_pin = digitalio.DigitalInOut(getattr(board, f"GP{MUTE_PIN}"))
        #mute_pin.direction = digitalio.Direction.OUTPUT
        #mute_pin.value = False  # Start muted
        #print("Mute pin initialized (started muted)")
        
        # Initialize I2S audio output
        print("Initializing I2S audio...")
        audio_out = audiobusio.I2SOut(
            bit_clock=getattr(board, f"GP{BCK_PIN}"),
            word_select=getattr(board, f"GP{WS_PIN}"),
            data=getattr(board, f"GP{SD_PIN}")
        )
        print("I2S audio initialized successfully")
                
        # Play simple tone
        if not audio_out.playing:
            print("Testing with simple tone...")
            import array
            import math
            
            # Generate a simple 440Hz sine wave
            sample_rate = 22050
            frequency = 440
            duration = 2.0
            samples = int(sample_rate * duration)
            
            # For 440Hz at 22050 samples/sec, this is about 50 samples
            samples_per_cycle = int(sample_rate / frequency)

            # Create a very small unsigned array
            sine_wave = array.array("H", [0] * samples_per_cycle)
            for i in range(samples_per_cycle):
                value = int(32767 * math.sin(2 * math.pi * i / samples_per_cycle))
                sine_wave[i] = value + 32768 

            print(f"Playing looping tone (Buffer size: {samples_per_cycle} samples)...")
            tone_sample = audiocore.RawSample(sine_wave, sample_rate=sample_rate)

            # Play with loop=True to keep it going
            audio_out.play(tone_sample, loop=True)

            # Let it play for 2 seconds
            time.sleep(2.0)

            audio_out.stop()
            print("Test tone completed")
            
            
            #print("Playing test tone (440Hz for 2 seconds)...")
            #audio_out.play(sine_wave, sample_rate=sample_rate)
            
            # Wait for tone to complete
            while audio_out.playing:
                time.sleep(0.1)
            print("Test tone completed")
        
        print("Playback completed!")
        
        # Clean up
        #print("Muting amplifier...")
        #mute_pin.value = False
        audio_out.stop()
        #mute_pin.deinit()
        print("Audio test completed successfully")
        
    except Exception as e:
        print(f"Error during audio test: {e}")
        import traceback
        traceback.print_exception(type(e), e, e.__traceback__)

if __name__ == "__main__":
    main()

