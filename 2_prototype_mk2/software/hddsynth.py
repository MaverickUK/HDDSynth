
"""
HDD Synth
Making HDDs loud again!
"""
import time
import activity
import audiobusio
import audiocore
import audiomixer 
import random
import digitalio
import board

import sample_changer
from sample_container import SampleContainer
import sdcard
import settings
import audio
import action_button
  
def run_synth():
    print("Starting HDD Synth...")
    print("HDD Sample Pack: " + sample_changer.get_desired_pack())

    # Pico LED
    led = digitalio.DigitalInOut(board.LED)
    led.direction = digitalio.Direction.OUTPUT

    # Ensure SD card is accessible
    sdcard.initilise()    

    # Init samples
    samples = {
        "jingle": SampleContainer(settings.JINGLE_FILE) if settings.PLAY_JINGLE else None,
        "spinup": SampleContainer(settings.SAMPLE_SPINUP_FILE),
        "idle": SampleContainer(settings.SAMPLE_IDLE_FILE),
        "access": SampleContainer(settings.SAMPLE_ACCESS_FILE)
    }

    # Initialize I2S audio output
    audio_out = audiobusio.I2SOut(
        bit_clock=settings.AMP_BCK_PIN,
        word_select=settings.AMP_WS_PIN,
        data=settings.AMP_SD_PIN
    )

    mixer = audiomixer.Mixer(
        voice_count=settings.MIXER_VOICES,
        sample_rate=samples["idle"].sample.sample_rate,
        channel_count=samples["idle"].sample.channel_count,
        bits_per_sample=samples["idle"].sample.bits_per_sample,
    )

    audio_out.play(mixer)
    audio.set_volume(mixer)


    if settings.PLAY_JINGLE:
        print('Playing jingle...')  
        audio.play_sample_active_pause2(mixer, samples["jingle"])

    if settings.PLAY_SPINUP:
        print('Playing spinup')
        audio.play_sample_active_pause2(mixer, samples["spinup"])
        print("Spin up complete")

    access = activity.get_access()

    # Auto loop, access controlled via volum 
    if settings.MIXER_VOICES == 2:
        mixer.voice[0].play(samples["idle"].sample, loop=True)
        mixer.voice[1].play(samples["access"].sample, loop=True)
        mixer.voice[1].level = 0 # Start with access muted


    while True:
        last_access = access
        access = activity.get_access()
        led.value = access
        activity.hdd_out(access)
        action_button.handler(mixer)

        if settings.MIXER_VOICES == 1:
            audio.set_volume(mixer)

            # If access state changes, stop current sample
            if last_access != access:
                    mixer.voice[0].stop()

            # Idle
            if not access and not mixer.voice[0].playing:
                mixer.voice[0].play(samples["idle"].sample)
                print(".", end="")

            # Access
            if access and not mixer.voice[0].playing:
                mixer.voice[0].play(samples["access"].sample)
                print(",", end="")

        elif settings.MIXER_VOICES == 2:
            audio.set_volume(mixer, access) # Mute access channel

        time.sleep(0.01)
    
if __name__ == "__main__":
    run_synth()