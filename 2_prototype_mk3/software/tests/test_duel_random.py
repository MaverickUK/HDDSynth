"""
test_duel_random.py

Loop both the idle and access WAVs from the SD card on separate mixer
voices. The access channel stays muted (volume 0.0) by default and has
a 10% chance each second to be unmuted (and the idle channel muted)
for the duration of the access sample.

Designed to run on-device (CircuitPython).
"""
import time
import audiocore
import audiobusio
import audiomixer
import random
import gc

import settings
import sdcard
import audio


def run(duration_seconds=30):
    sdcard.initilise()

    # Open files referenced in settings
    idle_fp = open(settings.SAMPLE_IDLE_FILE, "rb")
    access_fp = open(settings.SAMPLE_ACCESS_FILE, "rb")
    idle_wav = audiocore.WaveFile(idle_fp)
    access_wav = audiocore.WaveFile(access_fp)

    print("Idle:", idle_wav.sample_rate, idle_wav.channel_count, idle_wav.bits_per_sample)
    print("Access:", access_wav.sample_rate, access_wav.channel_count, access_wav.bits_per_sample)

    if (idle_wav.sample_rate != access_wav.sample_rate or
        idle_wav.channel_count != access_wav.channel_count or
        idle_wav.bits_per_sample != access_wav.bits_per_sample):
        print("WARNING: sample formats differ; results may be undefined")

    print("MEM_FREE at start:", end=" ")
    try:
        import gc as _gc
        print(_gc.mem_free())
    except Exception:
        print("(gc not available)")

    # Create audio out and mixer with defensive fallbacks. Some builds
    # of CircuitPython have differing `audiomixer.Mixer` signatures.
    try:
        audio_out = audiobusio.I2SOut(
            bit_clock=settings.AMP_BCK_PIN,
            word_select=settings.AMP_WS_PIN,
            data=settings.AMP_SD_PIN,
        )
    except Exception as e:
        print("Failed to initialize I2SOut:", e)
        try:
            idle_fp.close()
            access_fp.close()
        except Exception:
            pass
        return

    mixer_kwargs = {
        "voice_count": 2,
        "sample_rate": idle_wav.sample_rate,
        "channel_count": idle_wav.channel_count,
        "bits_per_sample": idle_wav.bits_per_sample,
    }
    # 16-bit samples are signed in WAVs; expose `samples_signed` where
    # supported to avoid mismatch errors.
    try:
        mixer_kwargs["samples_signed"] = True if getattr(idle_wav, "bits_per_sample", 16) > 8 else False
    except Exception:
        pass

    try:
        mixer = audiomixer.Mixer(**mixer_kwargs)
    except Exception as e:
        print("Mixer init failed with kwargs, retrying without samples_signed:", e)
        # Retry without samples_signed in case the runtime doesn't support it
        try:
            mixer = audiomixer.Mixer(
                voice_count=2,
                sample_rate=idle_wav.sample_rate,
                channel_count=idle_wav.channel_count,
                bits_per_sample=idle_wav.bits_per_sample,
            )
        except Exception as e2:
            print("Mixer init failed completely:", e2)
            try:
                audio_out.deinit()
            except Exception:
                pass
            try:
                idle_fp.close()
                access_fp.close()
            except Exception:
                pass
            return

    try:
        audio_out.play(mixer)
    except Exception as e:
        print("audio_out.play(mixer) failed:", e)
        try:
            audio_out.deinit()
        except Exception:
            pass
        try:
            idle_fp.close()
            access_fp.close()
        except Exception:
            pass
        return

    # Start both voices looping
    try:
        mixer.voice[0].play(idle_wav)
    except Exception as e:
        print("Failed to start idle voice:", e)
    try:
        mixer.voice[1].play(access_wav)
    except Exception as e:
        print("Failed to start access voice:", e)

    # Mute access initially, unmute idle
    try:
        mixer.voice[0].level = 1.0
    except Exception:
        pass
    try:
        mixer.voice[1].level = 0.0
    except Exception:
        pass

    # Determine how long an access trigger should remain unmuted
    try:
        access_duration = audio.get_duration(settings.SAMPLE_ACCESS_FILE, access_wav)
    except Exception:
        access_duration = 1.0

    in_access = False
    access_ends_at = 0

    start = time.monotonic()
    last_chance = start

    try:
        while time.monotonic() - start < duration_seconds:
            now = time.monotonic()

            # Each second, if not currently in access, roll a 10% chance
            if now - last_chance >= 1.0:
                last_chance = now
                if not in_access and random.random() < 0.10:
                    # Enter access: unmute access channel, mute idle
                    try:
                        mixer.voice[1].level = 1.0
                        mixer.voice[0].level = 0.0
                        in_access = True
                        access_ends_at = now + access_duration
                        print("Triggered access for", access_duration, "s")
                    except Exception as e:
                        print("Failed to switch volumes for access trigger:", e)

            # If access period ended, revert volumes
            if in_access and now >= access_ends_at:
                try:
                    mixer.voice[1].level = 0.0
                    mixer.voice[0].level = 1.0
                    in_access = False
                    print("Access finished; restored idle volume")
                except Exception as e:
                    print("Failed to restore volumes:", e)

            # Ensure both voices remain looping; if a voice stopped, restart it
            if not mixer.voice[0].playing:
                try:
                    idle_fp.seek(0)
                    mixer.voice[0].play(idle_wav)
                except Exception:
                    try:
                        idle_fp.close()
                    except Exception:
                        pass
                    idle_fp = open(settings.SAMPLE_IDLE_FILE, "rb")
                    idle_wav = audiocore.WaveFile(idle_fp)
                    mixer.voice[0].play(idle_wav)

            if not mixer.voice[1].playing:
                try:
                    access_fp.seek(0)
                    mixer.voice[1].play(access_wav)
                except Exception:
                    try:
                        access_fp.close()
                    except Exception:
                        pass
                    access_fp = open(settings.SAMPLE_ACCESS_FILE, "rb")
                    access_wav = audiocore.WaveFile(access_fp)
                    mixer.voice[1].play(access_wav)

            # Periodic memory housekeeping
            try:
                gc.collect()
            except Exception:
                pass

            time.sleep(0.01)

    finally:
        try:
            idle_fp.close()
        except Exception:
            pass
        try:
            access_fp.close()
        except Exception:
            pass
        try:
            audio_out.deinit()
        except Exception:
            pass


if __name__ == "__main__":
    print("Starting duel random test: idle always playing, access unmuted randomly")
    run(30)
    print("Test complete")
