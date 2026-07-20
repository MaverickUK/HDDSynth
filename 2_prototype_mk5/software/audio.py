import os
import time

import settings
import volume
import balance
import rotary_enc
import action_button


def stop_all(mixer):
    for i in range(settings.MIXER_VOICES):
        mixer.voice[i].stop()


def play_sample_active_pause(mixer, sample, level=None):
    """Play a sample on voice[0] and block until it finishes.

    If `level` is None, the user's current volume/balance are applied each tick.
    If `level` is a float, voice[0]'s level is pinned to that value (used for
    the jingle, which always plays at full volume).
    """
    if level is not None:
        mixer.voice[0].level = level

    mixer.voice[0].play(sample.sample)

    while mixer.voice[0].playing:
        if level is None:
            set_volume(mixer)
        action_button.handler(mixer)
        rotary_enc.handler(mixer)
        time.sleep(0.01)


def get_duration(filepath, wave_obj):
    file_size = os.stat(filepath)[6]
    # Subtract the standard WAV header
    data_size = file_size - 44
    bytes_per_second = (wave_obj.sample_rate * wave_obj.channel_count * (wave_obj.bits_per_sample // 8))
    return data_size / bytes_per_second


def set_volume(mixer, access=False):
    master = volume.get_volume()

    if settings.MIXER_VOICES == 1:
        mixer.voice[0].level = master
        return

    # Dual-voice: voice[0] is idle, voice[1] is access — apply balance between them.
    # voice[1] is silenced when the HDD isn't being accessed.
    bal = balance.get_balance()
    mixer.voice[0].level = master * (1.0 - bal)
    mixer.voice[1].level = master * bal if access else 0
