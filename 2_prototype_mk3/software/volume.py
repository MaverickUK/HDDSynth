import settings

_volume = settings.VOLUME_DEFAULT


def adjust(steps):
    """Adjust volume by `steps` encoder detents (positive = louder)."""
    global _volume
    _volume = max(0.0, min(1.0, _volume + steps * settings.VOLUME_STEP))
    if settings.VOLUME_PRINT:
        print(f"Volume: {int(_volume * 100)}%")


def get_volume():
    return _volume
