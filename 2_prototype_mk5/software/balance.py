import settings
from persisted_float import PersistedFloat

_state = PersistedFloat(
    default=settings.BALANCE_DEFAULT,
    step=settings.BALANCE_STEP,
    nvm_address=settings.NVM_ADDRESS_BALANCE,
)


def adjust(steps):
    """Adjust balance by `steps` encoder detents (positive = more access)."""
    if _state.adjust(steps) and settings.BALANCE_PRINT:
        print(f"Balance: {int(_state.get() * 100)}% access")


def get_balance():
    """0.0 = idle only, 1.0 = access only, 0.5 = equal mix."""
    return _state.get()


def persist_if_due():
    _state.persist_if_due()
