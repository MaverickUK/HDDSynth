import keypad
import board
import time

import beep
import sample_changer

# Action button state tracking
keys = keypad.Keys((board.GP1,), value_when_pressed=False, pull=True)

# Internal state tracking
_action_button_start_time = None
_action_button_long_pressed = False

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
                if duration < 1.0:
                    print("Short Press Detected (on release)")
                    beep.play_beep(mixer, pitch="high", count=1, length="short")
                    sample_changer.next_pack()

            _action_button_start_time = None # Reset
            
    # 2. Check for "Live" Long Press (while button is still held)
    if _action_button_start_time is not None and not _action_button_long_pressed:
        if (time.monotonic() - _action_button_start_time) >= 3.0:
            _action_button_long_pressed = True
            print("Long Pressed Detected (3 seconds held down)")
            beep.play_beep(mixer, pitch="high", count=1, length="long")