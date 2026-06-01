"""
HDD Synth
Making HDDs loud again! (MDDDLA)
"""
import time
import audiobusio
import audiomixer
import digitalio
import board
import microcontroller

import activity
import sample_changer
from sample_container import SampleContainer
import sdcard
import settings
import audio
import action_button
import rotary_enc
import power
import hdd_led
import nvm_wrapper


def _init_audio():
    """Bring up I2S out and the mixer. Returns (audio_out, mixer)."""
    audio_out = audiobusio.I2SOut(
        bit_clock=settings.AMP_BCK_PIN,
        word_select=settings.AMP_WS_PIN,
        data=settings.AMP_SD_PIN,
    )

    # One extra voice on top of MIXER_VOICES is reserved for beeps so they don't
    # interrupt the idle/access loops.
    mixer = audiomixer.Mixer(
        voice_count=settings.MIXER_VOICES + 1,
        sample_rate=settings.DEFAULT_SAMPLE_RATE,
        channel_count=settings.DEFAULT_CHANNEL_COUNT,
        bits_per_sample=settings.DEFAULT_BITS_PER_SAMPLE,
    )

    audio_out.play(mixer)
    return audio_out, mixer


def _load_samples():
    return {
        "jingle": SampleContainer(settings.JINGLE_FILE),
        "spinup": SampleContainer(settings.SAMPLE_SPINUP_FILE),
        "idle": SampleContainer(settings.SAMPLE_IDLE_FILE),
        "access": SampleContainer(settings.SAMPLE_ACCESS_FILE),
        "spindown": SampleContainer(settings.SAMPLE_SPINDOWN_FILE),
    }


def _maybe_play_jingle(mixer, samples):
    """Play the jingle at full volume the first time the device boots."""
    already_played = nvm_wrapper.safe_read(settings.NVM_ADDRESS_JINGLE) == settings.NVM_JINGLE_PLAYED
    if already_played and not settings.ALWAYS_PLAY_JINGLE:
        return

    print("Playing jingle...")
    audio.play_sample_active_pause(mixer, samples["jingle"], level=1.0)

    if not already_played:
        nvm_wrapper.write(settings.NVM_ADDRESS_JINGLE, settings.NVM_JINGLE_PLAYED)


def _start_dual_voice_loops(mixer, samples):
    """In dual-voice mode, the idle and access samples both loop continuously."""
    mixer.voice[0].play(samples["idle"].sample, loop=True)
    mixer.voice[1].play(samples["access"].sample, loop=True)
    mixer.voice[1].level = 0  # Start with access muted


def _main_loop(mixer, samples, led):
    """Run until external power is removed."""
    access = activity.get_access()

    if settings.MIXER_VOICES == 2:
        _start_dual_voice_loops(mixer, samples)

    while power.external_power():
        last_access = access
        access = activity.get_access()
        led.value = access
        hdd_led.set_active(access)
        action_button.handler(mixer)
        rotary_enc.handler(mixer)

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
            audio.set_volume(mixer, access=access)

        time.sleep(0.01)


def _spindown(mixer, samples):
    print("Playing spindown")
    audio.stop_all(mixer)
    audio.play_sample_active_pause(mixer, samples["spindown"])


def _wait_for_power_and_reset():
    while not power.external_power():
        time.sleep(0.1)
    microcontroller.reset()


def run_synth():
    print("Starting HDD Synth...")
    print("HDD Sample Pack: " + sample_changer.get_desired_pack())

    # Pico onboard LED — mirrors access state for dev visibility
    led = digitalio.DigitalInOut(board.LED)
    led.direction = digitalio.Direction.OUTPUT

    _, mixer = _init_audio()
    sdcard.initialise(mixer)
    samples = _load_samples()

    _maybe_play_jingle(mixer, samples)
    audio.set_volume(mixer)

    if settings.PLAY_SPINUP:
        print("Playing spinup")
        audio.play_sample_active_pause(mixer, samples["spinup"])
        print("Spin up complete")

    _main_loop(mixer, samples, led)
    _spindown(mixer, samples)
    _wait_for_power_and_reset()


if __name__ == "__main__":
    run_synth()
