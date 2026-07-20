import rotaryio
import keypad

import settings
import volume
import balance
import beep

MODE_VOLUME = 0
MODE_BALANCE = 1

_mode = MODE_VOLUME

_encoder = rotaryio.IncrementalEncoder(settings.ENCODER_A_PIN, settings.ENCODER_B_PIN)
_last_position = _encoder.position
_button = keypad.Keys((settings.ENCODER_BUTTON_PIN,), value_when_pressed=False, pull=True)


def handler(mixer):
    global _mode, _last_position

    # Encoder push button: toggle mode
    event = _button.events.get()
    if event and event.pressed:
        if _mode == MODE_VOLUME:
            _mode = MODE_BALANCE
            beep.play_beep_type(mixer, "BALANCE_MODE")
        else:
            _mode = MODE_VOLUME
            beep.play_beep_type(mixer, "VOLUME_MODE")

    # Encoder rotation: route delta to the active mode's state module
    position = _encoder.position
    delta = position - _last_position
    if delta != 0:
        _last_position = position
        if _mode == MODE_VOLUME:
            volume.adjust(delta)
        else:
            balance.adjust(delta)

    # Debounced NVM persistence
    volume.persist_if_due()
    balance.persist_if_due()
