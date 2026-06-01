import settings

_balance = settings.BALANCE_DEFAULT


def adjust(steps):
    """Adjust balance by `steps` encoder detents (positive = more access)."""
    global _balance
    _balance = max(0.0, min(1.0, _balance + steps * settings.BALANCE_STEP))
    if settings.BALANCE_PRINT:
        print(f"Balance: {int(_balance * 100)}% access")


def get_balance():
    """0.0 = idle only, 1.0 = access only, 0.5 = equal mix."""
    return _balance
