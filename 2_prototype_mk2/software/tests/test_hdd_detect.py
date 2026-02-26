"""
test_hdd_detect.py

Monitor GP26 (optocoupler pin 4) and print a message when activity
is detected. Pin 3 of the optocoupler is grounded; the opto output
pulls the line low on activity, so we enable an internal pull-up and
treat LOW as "activity".

Run on-device like:

    import tests.test_hdd_detect as d
    d.run(30)

"""
import time
import digitalio
import board

PIN = board.GP26
DEBOUNCE_MS = 10
POLL_INTERVAL = 0.01


def run(duration_seconds=None):
    """Monitor the optocoupler on `PIN` and print when activity is seen.

    If `duration_seconds` is None the function runs until interrupted.
    """
    d = digitalio.DigitalInOut(PIN)
    d.direction = digitalio.Direction.INPUT
    try:
        d.pull = digitalio.Pull.UP
    except Exception:
        # Some builds may not expose Pull; continue without explicit pull
        pass

    # Onboard LED to indicate activity
    led = digitalio.DigitalInOut(board.LED)
    led.direction = digitalio.Direction.OUTPUT
    led.value = False

    print("Monitoring optocoupler on", PIN, "(LOW == activity)")
    start = time.monotonic()
    last_state = d.value

    try:
        while True:
            if duration_seconds is not None and time.monotonic() - start >= duration_seconds:
                break

            state = d.value
            if state != last_state:
                # state changed; if it transitioned to LOW treat as activity
                if not state:
                    # debounce: confirm the line is still LOW after a short delay
                    time.sleep(DEBOUNCE_MS / 1000.0)
                    if not d.value:
                        ts = time.monotonic()
                        print(f"Activity detected at {ts:.3f}")
                        try:
                            led.value = True
                        except Exception:
                            pass
                else:
                    # Line went HIGH -> no activity
                    try:
                        led.value = False
                    except Exception:
                        pass
                last_state = state

            time.sleep(POLL_INTERVAL)
    finally:
        try:
            d.deinit()
        except Exception:
            pass
        try:
            led.value = False
            led.deinit()
        except Exception:
            pass


if __name__ == "__main__":
    print("Starting optocoupler monitor (GP26)")
    run()
