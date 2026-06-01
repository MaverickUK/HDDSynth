import audio
import keypad
import time

import beep
import sample_changer
import nvm_wrapper
import settings

# Action button state tracking
keys = keypad.Keys((settings.ACTION_BUTTON_PIN,), value_when_pressed=False, pull=True)

# Internal state tracking
_action_button_start_time = None
_action_button_long_pressed = False

def _factory_reset(mixer):
    print(f"Long Pressed Detected ({settings.ACTION_BUTTON_LONG_PRESS_S} seconds held down)")
    audio.stop_all(mixer)
    beep.play_beep_type(mixer, "FACTORY_RESET")

    sample_changer.wipe_settings()
    sample_changer.initialize() # Reset to first pack

    nvm_wrapper.safe_write(settings.NVM_ADDRESS_JINGLE, settings.NVM_JINGLE_NOT_PLAYED)
    nvm_wrapper.safe_write(settings.NVM_ADDRESS_MODE, settings.NVM_MODE_WRITE, reset=True)

def _change_pack(mixer):
    print("Short Press Detected (on release)")
    audio.stop_all(mixer)
    beep.play_beep_type(mixer, "CHANGE_PACK")
    sample_changer.next_pack()

def handler(mixer):
    global _action_button_start_time, _action_button_long_pressed
    
    event = keys.events.get()
    
    if event:
        if event.pressed:
            _action_button_start_time = time.monotonic()
            _action_button_long_pressed = False
        
        elif event.released:
            # Check for short press only if long press hasn't fired
            if not _action_button_long_pressed and _action_button_start_time is not None:
                duration = time.monotonic() - _action_button_start_time
                if duration < settings.ACTION_BUTTON_SHORT_PRESS_MAX_S:
                    _change_pack(mixer)

            _action_button_start_time = None # Reset
            
    # 2. Check for "Live" Long Press (while button is still held)
    if _action_button_start_time is not None and not _action_button_long_pressed:
        if (time.monotonic() - _action_button_start_time) >= settings.ACTION_BUTTON_LONG_PRESS_S:
            _action_button_long_pressed = True
            _factory_reset(mixer)

        