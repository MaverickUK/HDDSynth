import settings
from persisted_float import PersistedFloat

_state = PersistedFloat(
    default=settings.VOLUME_DEFAULT,
    step=settings.VOLUME_STEP,
    nvm_address=settings.NVM_ADDRESS_VOLUME,
)


def adjust(steps):
    """Adjust volume by `steps` encoder detents (positive = louder)."""
    if _state.adjust(steps) and settings.VOLUME_PRINT:
        print(f"Volume: {int(_state.get() * 100)}%")


def get_volume():
    return _state.get()


def persist_if_due():
    _state.persist_if_due()
