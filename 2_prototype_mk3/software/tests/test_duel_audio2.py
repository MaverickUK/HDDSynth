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
    last_gc = start
    try:
        while time.monotonic() - start < duration_seconds:
            now = time.monotonic()

            # Restart idle if finished. Recreate the WaveFile wrapper each
            # time rather than reusing an older WaveFile object which can
            # hold internal state; but be careful about memory pressure.
            if not mixer.voice[0].playing:
                try:
                    # Check memory before allocating new objects
                    mem_ok = True
                    try:
                        mem = gc.mem_free()
                        if mem < 20000:
                            mem_ok = False
                            print("Low memory, delaying idle restart:", mem)
                    except Exception:
                        mem_ok = True

                    if mem_ok:
                        try:
                            idle_fp.seek(0)
                            idle_wav = audiocore.WaveFile(idle_fp)
                            mixer.voice[0].play(idle_wav)
                            print("Loop idle")
                        except Exception as e:
                            print("Failed to restart idle voice:", e)
                    else:
                        # skip this cycle; try again later
                        pass
                except Exception as e:
                    print("Idle restart unexpected error:", e)

            # Restart access if finished (same strategy)
            if not mixer.voice[1].playing:
                try:
                    mem_ok = True
                    try:
                        mem = gc.mem_free()
                        if mem < 20000:
                            mem_ok = False
                            print("Low memory, delaying access restart:", mem)
                    except Exception:
                        mem_ok = True

                    if mem_ok:
                        try:
                            access_fp.seek(0)
                            access_wav = audiocore.WaveFile(access_fp)
                            mixer.voice[1].play(access_wav)
                            print("Loop access")
                        except Exception as e:
                            print("Failed to restart access voice:", e)
                    else:
                        pass
                except Exception as e:
                    print("Access restart unexpected error:", e)

            # Throttle garbage collection to once per second to avoid
            # creating jitter and fragmentation from frequent collections.
            try:
                if now - last_gc >= 1.0:
                    gc.collect()
                    last_gc = now
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
