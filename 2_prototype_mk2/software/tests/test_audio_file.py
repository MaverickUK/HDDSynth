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
BCK_PIN = 16# 26#10 #26    # I2S Bit Clock (BCK / SCLK)
WS_PIN = 17# 27#11 #27     # I2S Word Select / LRCK  
SD_PIN = 18# 28#9 #28     # I2S Data (SD / DIN)
# MUTE_PIN = 22   # Mute pin (active low - False = unmuted, True = muted)

def play_file(filename):
    print("Audio playback starting")
    print(f"Using pins: BCK=GP{BCK_PIN}, WS=GP{WS_PIN}, SD=GP{SD_PIN}")
    
    try:        
        # Initialize I2S audio output
        print("Initializing I2S audio...")
        audio_out = audiobusio.I2SOut(
            bit_clock=getattr(board, f"GP{BCK_PIN}"),
            word_select=getattr(board, f"GP{WS_PIN}"),
            data=getattr(board, f"GP{SD_PIN}")
        )
        print("I2S audio initialized successfully")
        
        print("Loading WAV file from SD card...")
        try:
            # List available files first
            import os
            
            files = os.listdir('/sd')
            wav_files = [f for f in files if f.endswith('.wav')]
            print(f"Available WAV files on SD card: {wav_files}")
        
            wave_file = audiocore.WaveFile(open(filename, "rb"))
            
            
            print("WAV file loaded successfully")
            print(f"Audio format: {wave_file.sample_rate}Hz, {wave_file.bits_per_sample}bit, {wave_file.channel_count} channel(s)")
        except OSError as e:
            print(f"Error loading WAV file: {e}")
            return
        
        # Play the audio file
        print("Playing audio file...")
        audio_out.play(wave_file)
        
        # Wait for playback to complete
        print("Waiting for playback to complete...")
        while audio_out.playing:
            time.sleep(0.1)

        print("Playback completed!")
        
        audio_out.stop()
        print("Audio test completed successfully")
        
    except Exception as e:
        print(f"Error during audio test: {e}")
        import traceback
        traceback.print_exception(type(e), e, e.__traceback__)

#if __name__ == "__main__":
#    main()

