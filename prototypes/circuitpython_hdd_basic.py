# SPDX-FileCopyrightText: 2021 Kattni Rembor for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
CircuitPython I2S MP3 playback example.
Plays a single MP3 once.
"""
import board
import audiocore
import audiomp3
import audiobusio
import audiomixer
import time
from digitalio import DigitalInOut, Direction, Pull

# import adafruit_character_lcd.character_lcd_i2c as character_lcd

import random

import analogio

num_voices = 2

# Print out input voltage
DEBUG_VOLTAGE_INPUT = False

# Simulate random HDD access
SIMUALATION_MODE = True

# Trigger voltage for detecting HDD LED activity
HDD_TRIGGER_VOLTAGE = 1.2 # Max 3.3v

# Delay after a change of HDD activity state
HDD_STATE_CHANGE_DELAY = 0.05

# https://github.com/todbot/circuitpython-tricks

audio = audiobusio.I2SOut(board.GP10, board.GP11, board.GP9)

# sample_rate=22050

mixer = audiomixer.Mixer(voice_count=num_voices, sample_rate=16000, channel_count=1,
                         bits_per_sample=16, samples_signed=True)

audio.play(mixer) # attach mixer to audio playback

# spinup = audiomp3.MP3Decoder(open("nec_startup_16hz_16bit.wav", "rb"))
# idle = audiocore.WaveFile(open("nec_idle_16hz_16bit.wav", "rb")) # Wave file loop smoothly

# HDD access detection
hdd = DigitalInOut(board.GP15)
hdd.direction = Direction.INPUT
hdd.pull = Pull.UP

# External HDD LED
hdd_led = DigitalInOut(board.GP14)
hdd_led.direction = Direction.OUTPUT

# Onboard LED
led = DigitalInOut(board.GP25)
led.direction = Direction.OUTPUT

# HDD LED input
hdd_input = analogio.AnalogIn(board.GP28) # GP28
hdd_offset = analogio.AnalogIn(board.GP27) 

# https://learn.adafruit.com/circuitpython-libraries-on-any-computer-with-raspberry-pi-pico/adc
def get_voltage():
    # raw = hdd_input.value
    # return (raw * 3.3) / 65536
    
    get_voltage = 3.3 / 65535
    
    # Average out a number of readings: https://forums.raspberrypi.com/viewtopic.php?t=338514
    total = 0.0
    filter = 32
    
    for x in range(0,filter):
        reading = hdd_input.value # - hdd_offset.value
        total += reading
        
    reading = total / filter

    voltage = reading * get_voltage # Display voltage based on 3.3V reference
    return voltage

while DEBUG_VOLTAGE_INPUT and True:
   volts = get_voltage()
   print("volts = {:5.2f}".format(volts))
   time.sleep(0.5)

#led = Pin(25, Pin.OUT)

spinup = audiocore.WaveFile(open("nec_spinup_16hz_16bit.wav", "rb"))
idle = audiocore.WaveFile(open("nec_idle_long_16hz_16bit.wav", "rb"))
access = audiocore.WaveFile(open("nec_access_16hz_16bit.wav", "rb"))

print("Spinning disk up")
# mixer.voice[0].play( spinup )
audio.play(spinup)
# time.sleep(11)

while audio.playing:
   pass

print("Disk spun up")

# Remember the previous HDD access value
last_hdd = False
hddOn = False

count = 0

while True:
    if SIMUALATION_MODE:
        if count > 5000:
            rnd = random.random()
            if rnd > 0.3:
                hddOn = True
            else:
                hddOn = False
                
            count = 0
        else:
            count = count + 1
    else: # Read actual HDD activity
        hddOn = hdd.value == False

        # Trigger HDD activity from monitoring input HDD LED activity
        if hddOn == False:
            hdd_voltage = get_voltage()
            hddOn = hdd_voltage > HDD_TRIGGER_VOLTAGE

    # Show disk activity
    led.value = hddOn 
    hdd_led.value = hddOn
    
    # Start playing sample on HDD activity change
    if hddOn != last_hdd:
        if hddOn:
            print("Access")
            audio.play(access)
            
            # If disk activity is too quick is causes audio issues
            time.sleep(HDD_STATE_CHANGE_DELAY)  
        else:
            print("Idling")
            audio.play(idle)
            
            # If disk activity is too quick is causes audio issues
            time.sleep(HDD_STATE_CHANGE_DELAY)              
            
    # Loop sample if stopped
    if not audio.playing:
        if hddOn:
            audio.play(access)
        else:
            # print("Idling")
            audio.play(idle)
    
    last_hdd = hddOn
    
    # time.sleep(0.05)    

# while audio.playing:
#      pass
# 
# mixer.voice[1].play( idle, loop=True) # start each one playing
# 
# 
# while True:
#     print("Idling")
#     time.sleep(10)
#     
#     print("Disk access")
#     mixer.voice[0].play( access )


#wav_file = "/amen1_22k_s16.wav" # in 'circuitpython-tricks/larger-tricks/breakbeat_wavs'
#mp3_file = "/vocalchops476663_22k_128k.mp3" # in 'circuitpython-tricks/larger-tricks/wav'
# https://freesound.org/people/f-r-a-g-i-l-e/sounds/476663/

# wave = audiocore.WaveFile(open("nec_idle.wav", "rb"))
# wave = audiomp3.MP3Decoder(open("nec_idle.wav", "rb"))
# wave = audiocore.WaveFile(open("nec_idle.wav", "rb"))
# mp3 = audiocore.WaveFile(open("nec_startup.wav", "rb"))
# mixer.voice[0].play( wave )
# mixer.voice[1].play( mp3 )
# 
# while True:
#     pass   # both audio files play


# # Hard drive startup
# def play_startup():
#     audio.play(mp3_startup)
# 
#     while audio.playing:
#         pass
# 
# play_startup()
# 
# audio.play(mp3_idle, loop = True)
# 
# while audio.playing:
#     pass    








