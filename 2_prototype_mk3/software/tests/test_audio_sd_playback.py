# Read wav samples from SD card and play back using the amp

import sys

# Allow other test scripts to be referenced
sys.path.append("/tests")

import time
import board
import digitalio
import audiobusio
import audiocore

import test_sdcard
import test_audio_file_with_volume

def main():
    print("Audio from SD card test starting...")

    # Test 1: SPI connection
    spi, cs = test_sdcard.test_spi_connection()
    if not spi:
        print("\n❌ DIAGNOSTIC FAILED: Cannot initialize SPI")
        return
    
    # Test 2: SD card detection
    sd = test_sdcard.test_sd_card_detection(spi, cs)
    if not sd:
        print("\n❌ DIAGNOSTIC FAILED: Cannot detect SD card")
        return
    
    # Test 3: Mount filesystem
    if not test_sdcard.mount_sd_card(sd):
        print("\n❌ DIAGNOSTIC FAILED: Cannot mount SD card")
        return
    
    # Play spinup from sdcard
    test_audio_file_with_volume.play_file("sd/spinup.wav")
    
    # Play idle
    test_audio_file_with_volume.play_file("sd/idle.wav")
    test_audio_file_with_volume.play_file("sd/access.wav")
    test_audio_file_with_volume.play_file("sd/idle.wav")    
    

if __name__ == "__main__":
    main()