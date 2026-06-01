import rotaryio

import settings

encoder = rotaryio.IncrementalEncoder(settings.ENCODER_A_PIN, settings.ENCODER_B_PIN)

_last_position = encoder.position
_volume = settings.VOLUME_DEFAULT


def get_volume():
    global _last_position, _volume

    position = encoder.position
    delta = position - _last_position

    if delta != 0:
        _last_position = position
        _volume = max(0.0, min(1.0, _volume + delta * settings.VOLUME_STEP))
        if settings.VOLUME_PRINT:
            print(f"Volume: {int(_volume * 100)}%")

    return _volume
