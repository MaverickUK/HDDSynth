"""
test_duel_audio.py

Play both the idle and access WAVs simultaneously on separate mixer
voices, looping both files from the SD card. Uses the filenames in
`settings.py` and calls `sdcard.initilise()`.

Designed to run on-device (CircuitPython).
"""
import time
import audiocore
import audiobusio
import audiomixer
import gc

import settings
import sdcard


def run(duration_seconds=30):
    """Play both idle and access samples on separate mixer voices for
    `duration_seconds` seconds. Both files are streamed from the SD card
    and looped by seeking back to start when they finish.
    """
    sdcard.initilise()

    # Open files from settings
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

    samples_signed = True if getattr(idle_wav, 'bits_per_sample', 16) > 8 else False

    audio_out = audiobusio.I2SOut(
        bit_clock=settings.AMP_BCK_PIN,
        word_select=settings.AMP_WS_PIN,
        data=settings.AMP_SD_PIN,
    )

    mixer = audiomixer.Mixer(
        voice_count=2,
        sample_rate=idle_wav.sample_rate,
        channel_count=idle_wav.channel_count,
        bits_per_sample=idle_wav.bits_per_sample,
        samples_signed=samples_signed,
    )

    audio_out.play(mixer)

    # Start playback on both voices
    try:
        mixer.voice[0].play(idle_wav)
    except Exception as e:
        print("Failed to start idle voice:", e)

    try:
        mixer.voice[1].play(access_wav)
    except Exception as e:
        print("Failed to start access voice:", e)

    start = time.monotonic()
    try:
        while time.monotonic() - start < duration_seconds:
            # Restart idle if finished
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

            # Restart access if finished
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

            # Periodically free memory
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
    print("Starting duel audio test: looping both idle and access on separate voices")
    run(30)
    print("Test complete")
