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
import sd_settings
import beep


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
    jingle = None
    try:
        jingle = SampleContainer(settings.JINGLE_FILE)
    except OSError:
        print(f"[hddsynth] Jingle not found: {settings.JINGLE_FILE}")

    paths = sample_changer.get_sample_paths()
    return {
        "jingle":   jingle,
        "spinup":   SampleContainer(paths["spinup"]),
        "idle":     SampleContainer(paths["idle"]),
        "access":   SampleContainer(paths["access"]),
        "spindown": SampleContainer(paths["spindown"]),
    }


def _maybe_play_jingle(mixer, samples):
    """Play the jingle at full volume the first time the device boots."""
    already_played = nvm_wrapper.safe_read(settings.NVM_ADDRESS_JINGLE) == settings.NVM_JINGLE_PLAYED
    if already_played and not settings.ALWAYS_PLAY_JINGLE:
        return

    if samples["jingle"] is None:
        print("[hddsynth] Skipping jingle — file not found.")
        return

    print("Playing jingle...")
    audio.play_sample_active_pause(mixer, samples["jingle"], level=1.0)

    if not already_played:
        nvm_wrapper.write(settings.NVM_ADDRESS_JINGLE, settings.NVM_JINGLE_PLAYED)


def _start_dual_voice_loops(mixer, samples):
    """In dual-voice mode, the idle and access samples both loop continuously."""
    if settings.PLAY_IDLE:
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
            if not access and not mixer.voice[0].playing and settings.PLAY_IDLE:
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
    if settings.PLAY_SPINDOWN:
        print("Playing spindown")
        audio.stop_all(mixer)
        audio.play_sample_active_pause(mixer, samples["spindown"])


def _apply_sd_settings(sd_overrides):
    """Apply settings overrides loaded from SD card."""
    if "SIMULATION_MODE" in sd_overrides:
        settings.SIMULATION_MODE = sd_overrides["SIMULATION_MODE"]
        print(f"[SD Settings] SIMULATION_MODE = {settings.SIMULATION_MODE}")
    if "PLAY_SPINUP" in sd_overrides:
        settings.PLAY_SPINUP = sd_overrides["PLAY_SPINUP"]
        print(f"[SD Settings] PLAY_SPINUP = {settings.PLAY_SPINUP}")
    if "PLAY_SPINDOWN" in sd_overrides:
        settings.PLAY_SPINDOWN = sd_overrides["PLAY_SPINDOWN"]
        print(f"[SD Settings] PLAY_SPINDOWN = {settings.PLAY_SPINDOWN}")
    if "PLAY_IDLE" in sd_overrides:
        settings.PLAY_IDLE = sd_overrides["PLAY_IDLE"]
        print(f"[SD Settings] PLAY_IDLE = {settings.PLAY_IDLE}")
    if "ACCESS_HOLD_TIME_MS" in sd_overrides:
        settings.ACCESS_HOLD_TIME_MS = sd_overrides["ACCESS_HOLD_TIME_MS"]
        print(f"[SD Settings] ACCESS_HOLD_TIME_MS = {settings.ACCESS_HOLD_TIME_MS}")
    if "VOLUME_DEFAULT" in sd_overrides:
        settings.VOLUME_DEFAULT = sd_overrides["VOLUME_DEFAULT"]
        print(f"[SD Settings] VOLUME_DEFAULT = {settings.VOLUME_DEFAULT}")
    if "BALANCE_DEFAULT" in sd_overrides:
        settings.BALANCE_DEFAULT = sd_overrides["BALANCE_DEFAULT"]
        print(f"[SD Settings] BALANCE_DEFAULT = {settings.BALANCE_DEFAULT}")
    if "SDCARD_CACHE_SAMPLES" in sd_overrides:
        settings.SDCARD_CACHE_SAMPLES = sd_overrides["SDCARD_CACHE_SAMPLES"]
        print(f"[SD Settings] SDCARD_CACHE_SAMPLES = {settings.SDCARD_CACHE_SAMPLES}")


def _make_reload_callback(samples):
    """Returns a closure that hot-swaps the active sample pack in-place."""
    def reload(mixer):
        audio.stop_all(mixer)
        try:
            new_samples = _load_samples()
        except Exception as e:
            print(f"[hddsynth] Pack reload failed: {e}")
            if settings.MIXER_VOICES == 2:
                _start_dual_voice_loops(mixer, samples)
            return
        for s in samples.values():
            if s is not None:
                s.deinit()
        samples.update(new_samples)
        if settings.MIXER_VOICES == 2:
            _start_dual_voice_loops(mixer, samples)
        print("HDD Sample Pack: " + sample_changer.get_desired_pack())
    return reload


def _no_op_action_button_handler(mixer):
    """No-op handler when action button is disabled."""
    pass


def _wait_for_power_and_reset():
    while not power.external_power():
        time.sleep(0.1)
    microcontroller.reset()


def _check_sample_pack_installed():
    """Check if a sample pack is installed (by checking if desired pack is set)."""
    return bool(sample_changer.get_desired_pack())


def run_synth():
    print("Starting HDD Synth...")

    # Pico onboard LED — mirrors access state for dev visibility
    led = digitalio.DigitalInOut(board.LED)
    led.direction = digitalio.Direction.OUTPUT

    _, mixer = _init_audio()

    # Try to initialize SD card
    sd_available = sdcard.initialise(mixer)

    # Load and apply settings from SD card if available
    if sd_available:
        sd_overrides = sd_settings.load_settings()
        _apply_sd_settings(sd_overrides)
    else:
        sd_overrides = {}

    # Check if sample pack is installed
    sample_pack_installed = _check_sample_pack_installed()

    # Handle SDCARD_REQUIRED logic
    if not sd_available:
        if settings.SDCARD_REQUIRED or not settings.SDCARD_CACHE_SAMPLES:
            print("[hddsynth] SD card required but not available, exiting")
            beep.play_beep_type(mixer, "NO_SD_CARD")
            _wait_for_power_and_reset()
            return

        if not sample_pack_installed:
            print("[hddsynth] No sample pack installed and SD card not available, playing error beep")
            beep.play_beep_type(mixer, "PACK_NOT_FOUND")
            _wait_for_power_and_reset()
            return

        print("[hddsynth] SD card not available but sample pack is installed, disabling action button")
        action_button.handler = _no_op_action_button_handler

    print("HDD Sample Pack: " + sample_changer.get_desired_pack())

    # Handle sample pack installation from SD card (only if SD is available)
    if sd_available:
        pack_install_ok = sd_settings.install_sample_pack_if_needed(sd_overrides)
        if not pack_install_ok:
            print("[hddsynth] Sample pack from SD settings not found, playing error beep")
            beep.play_beep_type(mixer, "PACK_NOT_FOUND")

    samples = _load_samples()

    if not settings.SDCARD_CACHE_SAMPLES:
        action_button.set_reload_callback(_make_reload_callback(samples))

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
