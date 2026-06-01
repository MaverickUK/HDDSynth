"""
test_audio_streaming.py

Test that we can stream an "idle" WAV from the SD card while a smaller
"access" WAV is loaded into RAM and played on a second mixer voice.

This test is designed to run on-device (CircuitPython) and is a functional
smoke-test rather than a unit test framework file. It follows the patterns
used in the existing tests directory.
"""
import time
import audiocore
import gc
import audiobusio
import audiomixer
import random

import settings
import sdcard
import audio


def run(duration_seconds=10):
    """Run the streaming test for `duration_seconds` seconds.

    - Streams the idle file from SD on mixer.voice[0]
    - Loads access file into RAM and plays it on mixer.voice[1] at random
      intervals while the idle stream continues.
    """
    # Ensure SD is initialised (tests in this repo call sdcard.initilise())
    sdcard.initilise()
    

    # Open the idle WaveFile directly from SD (streamed)
    idle_fp = open("sd/idle_11khz_8bit.wav", "rb")
    idle_wav = audiocore.WaveFile(idle_fp)


    # Load access into RAM using the strict helper so we validate format.
    # If we run out of RAM, fall back to streaming the access file from SD.
    access_fp = None
    try:
        access_raw = audio.load_to_ram_with_expected(
            "sd/access_11khz_8bit.wav",
            expected_sample_rate=idle_wav.sample_rate,
            expected_channel_count=idle_wav.channel_count,
            expected_bits_per_sample=idle_wav.bits_per_sample,
        )
        print("Loaded access sample into RAM")
    except (MemoryError, OSError) as e:
        print("WARNING: could not load access sample into RAM; falling back to streamed playback:", e)
        access_fp = open("sd/access_11khz_8bit.wav", "rb")
        access_raw = audiocore.WaveFile(access_fp)

    # Create audio out & mixer
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
        samples_signed=True,
    )
    audio_out.play(mixer)

    # Start the idle stream on voice 0
    mixer.voice[0].play(idle_wav)

    start = time.monotonic()
    last_trigger = start
    trigger_interval = 1.0  # minimum spacing between triggers
    last_mem_report = start
    current_access_wav = None

    try:
        while time.monotonic() - start < duration_seconds:
            # Randomly trigger access sample (roughly once per 3-5 seconds)
            # Periodic memory report
            if time.monotonic() - last_mem_report >= 1.0:
                try:
                    print("MEM_FREE:", gc.mem_free())
                except Exception:
                    pass
                last_mem_report = time.monotonic()

            if time.monotonic() - last_trigger >= trigger_interval:
                if random.random() < 0.02:
                    # Debug: show mixer/sample metadata before playing
                    print("DEBUG: mixer.bits_per_sample=", getattr(mixer, 'bits_per_sample', None))
                    print("DEBUG: idle_wav.bits_per_sample=", getattr(idle_wav, 'bits_per_sample', None))
                    print("DEBUG: access_raw type=", type(access_raw))
                    print("DEBUG: access_raw.bits_per_sample=", getattr(access_raw, 'bits_per_sample', None))
                    print("DEBUG: access_raw.sample_rate=", getattr(access_raw, 'sample_rate', None))
                    print("DEBUG: access_raw.channel_count=", getattr(access_raw, 'channel_count', None))
                    # Check available RAM before attempting playback to avoid crashing
                    try:
                        gc.collect()
                    except Exception:
                        pass
                    mem_free = None
                    try:
                        mem_free = gc.mem_free()
                    except Exception:
                        pass

                    if mem_free is not None and mem_free < 120000:
                        print("Skipping access playback; low memory:", mem_free)
                    else:
                        # If access is streamed from SD, recreate a fresh WaveFile
                        # wrapper from the same open file so internal WaveFile state
                        # is reset for playback; keep a reference until playback ends.
                        try:
                            if 'access_fp' in locals() and access_fp:
                                access_fp.seek(0)
                                current_access_wav = audiocore.WaveFile(access_fp)
                                try:
                                    mixer.voice[1].play(current_access_wav)
                                except Exception as e:
                                    print("Failed to play streamed access sample:", e)
                                    current_access_wav = None
                            else:
                                try:
                                    mixer.voice[1].play(access_raw)
                                except Exception as e:
                                    print("Failed to play RAM access sample:", e)
                        except Exception as e:
                            print("Access playback setup failed:", e)
                    # Try to free memory immediately after scheduling playback
                    try:
                        gc.collect()
                    except Exception:
                        pass
                    last_trigger = time.monotonic()

            # If the idle voice finished (end of file), restart it to simulate looped streaming
            if not mixer.voice[0].playing:
                # Try to replay the same WaveFile by seeking back to start;
                # this avoids allocating new WaveFile/file objects repeatedly.
                try:
                    idle_fp.seek(0)
                    mixer.voice[0].play(idle_wav)
                except Exception:
                    # Fallback: recreate the file and WaveFile if seek fails
                    try:
                        idle_fp.close()
                    except Exception:
                        pass
                    idle_fp = open(settings.SAMPLE_IDLE_FILE, "rb")
                    idle_wav = audiocore.WaveFile(idle_fp)
                    mixer.voice[0].play(idle_wav)
                try:
                    gc.collect()
                except Exception:
                    pass

            # If a streamed access WaveFile finished, drop our reference so
            # it can be garbage-collected and free memory.
            if current_access_wav is not None and not mixer.voice[1].playing:
                current_access_wav = None
                try:
                    gc.collect()
                except Exception:
                    pass

            time.sleep(0.01)

    finally:
        # Cleanup
        try:
            idle_fp.close()
        except Exception:
            pass
        if access_fp:
            try:
                access_fp.close()
            except Exception:
                pass
        try:
            audio_out.deinit()
        except Exception:
            pass


if __name__ == "__main__":
    print("Starting test_audio_streaming: streaming idle from SD, RAM access on voice 1")
    run(30)
    print("Test complete")
    