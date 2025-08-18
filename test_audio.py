"""
Simple I2S Pin Test for Pico Audio Pack
Tests basic pin functionality without complex audio processing.
"""

import time
import board
import digitalio

# Audio pin configuration for Pico Audio Pack (default pinout)
BCK_PIN = 9     # I2S Bit Clock (BCK / SCLK) - GP9
WS_PIN = 10     # I2S Word Select / LRCK - GP10  
SD_PIN = 11     # I2S Data (SD / DIN) - GP11
MUTE_PIN = 8    # Mute pin (active low) - GP8

def test_pin_toggle(pin_number, pin_name, duration=1):
    """Test a pin by toggling it rapidly."""
    print(f"Testing {pin_name} (GP{pin_number}) - toggling for {duration} second...")
    
    try:
        pin = digitalio.DigitalInOut(getattr(board, f"GP{pin_number}"))
        pin.direction = digitalio.Direction.OUTPUT
        
        start_time = time.monotonic()
        while time.monotonic() - start_time < duration:
            pin.value = True
            time.sleep(0.001)  # 1ms high
            pin.value = False
            time.sleep(0.001)  # 1ms low
        
        pin.deinit()
        print(f"  {pin_name} test completed")
        
    except Exception as e:
        print(f"  Error testing {pin_name}: {e}")

def test_mute_pin():
    """Test mute pin functionality."""
    print("Testing mute pin (GP22)...")
    
    try:
        mute_pin = digitalio.DigitalInOut(getattr(board, f"GP{MUTE_PIN}"))
        mute_pin.direction = digitalio.Direction.OUTPUT
        
        print("  Setting mute pin HIGH (muted)...")
        mute_pin.value = True
        time.sleep(2)
        
        print("  Setting mute pin LOW (unmuted)...")
        mute_pin.value = False
        time.sleep(2)
        
        print("  Setting mute pin HIGH (muted)...")
        mute_pin.value = True
        time.sleep(1)
        
        mute_pin.deinit()
        print("  Mute pin test completed")
        
    except Exception as e:
        print(f"  Error testing mute pin: {e}")

def main():
    print("Simple I2S Pin Test for Pico Audio Pack")
    print("=" * 40)
    print("This test will toggle each I2S pin rapidly.")
    print("You should hear clicking/static if wiring is correct.")
    print("")
    
    # Test mute pin first
    test_mute_pin()
    print("")
    
    # Test each I2S pin individually
    test_pin_toggle(BCK_PIN, "BCK (Bit Clock)", 2)
    print("")
    test_pin_toggle(WS_PIN, "WS (Word Select)", 2)
    print("")
    test_pin_toggle(SD_PIN, "SD (Serial Data)", 2)
    print("")
    
    print("Pin test completed!")
    print("")
    print("Expected results:")
    print("- You should hear clicking/static when each pin toggles")
    print("- Mute pin should control whether you hear the clicks")
    print("- If you hear nothing, check your wiring:")
    print("  • GP9  → BCK on Audio Pack")
    print("  • GP10 → WS on Audio Pack") 
    print("  • GP11 → SD on Audio Pack")
    print("  • GP8  → MUTE on Audio Pack")
    print("  • 3.3V → 3.3V on Audio Pack")
    print("  • GND → GND on Audio Pack")
    print("")
    print("Note: This uses the DEFAULT Pico Audio Pack pinout.")
    print("If you have custom wiring, update the pin numbers above.")

if __name__ == "__main__":
    main()
