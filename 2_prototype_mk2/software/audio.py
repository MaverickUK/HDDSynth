import os
import audiobusio
import audiocore
import time
import array


import settings
import volume
import action_button

def play_sample_active_pause2(mixer, sample):
    mixer.voice[0].play(sample.sample)

    while (mixer.voice[0].playing):
        set_volume(mixer)
        action_button.handler(mixer)
        time.sleep(0.01)

def play_sample_active_pause(mixer, sample_container):
    seconds = sample_container.duration

    print("Activing pause for", seconds, "seconds")
    start_time = time.monotonic()

    # Ensure we play from the start by seeking the underlying file and
    # creating a fresh WaveFile wrapper. Reusing a long-lived WaveFile
    # can leave its internal file pointer at EOF which results in no
    # audible playback for subsequent plays.
    wf = None
    try:
        try:
            sample_container.file_handle.seek(0)
        except Exception:
            pass

        try:
            wf = audiocore.WaveFile(sample_container.file_handle)
        except Exception as e:
            print("Failed to create WaveFile for active pause:", e)
            return

        print("Starting playback:", getattr(sample_container, 'sample_file', '<unknown>'))
        mixer.voice[0].play(wf)

        while (time.monotonic() - start_time) < seconds:
            set_volume(mixer)
            # Micro-sleep to keep the CPU stable and prevent USB dropouts
            time.sleep(0.01)
    finally:
        # Try to deinit the temporary WaveFile to free any internal
        # resources; ignore if not available on this build.
        try:
            if wf is not None:
                wf.deinit()
        except Exception:
            pass


def get_duration(filepath, wave_obj):
    # 1. Get the size of the file in bytes from the SD card
    file_size = os.stat(filepath)[6] 
    
    # 2. Subtract the standard WAV header (usually 44 bytes)
    data_size = file_size - 44
    
    # 3. Calculate how many bytes are played per second
    # Formula: (Sample Rate * Channels * (Bits Per Sample / 8))
    bytes_per_second = (wave_obj.sample_rate * wave_obj.channel_count * (wave_obj.bits_per_sample // 8))
    
    return data_size / bytes_per_second

def set_volume(mixer, access=True):
    for i in range(settings.MIXER_VOICES):
        mixer.voice[i].level = volume.get_volume()

    # Mute access in dual voice mode
    if settings.MIXER_VOICES == 2 and not access:
        mixer.voice[1].level = 0

def play_sample(filename):
    audio_out = audiobusio.I2SOut(
    bit_clock=settings.AMP_BCK_PIN,
    word_select=settings.AMP_WS_PIN,
    data=settings.AMP_SD_PIN)

    # 2. Open the file in 'rb' (read binary) mode
    # Pass the file handle to audiocore.WaveFile
    with open(filename, "rb") as wave_file:
        wav = audiocore.WaveFile(wave_file)
        
        print(f"Playing {filename}...")
        audio_out.play(wav)

        while audio_out.playing:
            pass
            
    # Clean up hardware to free up resources
    audio_out.deinit()
    print("Finished playing.")
