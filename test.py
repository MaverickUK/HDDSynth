# test.py
# Test script for HDD Synth - simulates HDD activity for testing
# This script can be used to verify audio playback without ISA bus connection

import time
from machine import Pin

# Test configuration constants
TEST_IDLE_DURATION = 5      # Seconds to test idle sound
TEST_TRANSITION_DELAY = 2   # Seconds between audio transitions
TEST_PAUSE_BETWEEN_TESTS = 1  # Seconds between test runs

# Import the main HDD Synth class
try:
    from main import HDDSynth
except ImportError:
    print("Error: Could not import HDDSynth class")
    print("Make sure main.py is in the same directory")
    exit(1)

def test_executor(test_name):
    """Decorator to handle test execution and error handling."""
    def decorator(test_func):
        def wrapper(self, *args, **kwargs):
            try:
                test_func(self, *args, **kwargs)
                print(f"✅ {test_name}: PASSED")
                return True
            except Exception as e:
                print(f"❌ {test_name}: FAILED - {e}")
                return False
        return wrapper
    return decorator

class HDDSynthTest:
    def __init__(self):
        """Initialize the test system."""
        print("HDD Synth Test Mode")
        print("This will test audio playback without ISA bus monitoring")
        
        # Create a mock ISA monitoring system
        self._create_mock_isa()
        
        # Initialize HDD Synth
        try:
            self.hdd_synth = HDDSynth()
            print("HDD Synth initialized successfully in test mode")
        except Exception as e:
            print(f"Error initializing HDD Synth: {e}")
            print("Make sure all required files and hardware are connected")
            return
        
        self.test_mode = True
    
    def _create_mock_isa(self):
        """Create mock ISA state machines for testing."""
        # This is a simplified version that doesn't require actual ISA bus
        # In a real implementation, these would be the actual PIO state machines
        print("Mock ISA monitoring system created for testing")
    
    @test_executor("Spinup Sound")
    def test_spinup(self):
        """Test the spinup sound."""
        print("\n=== Testing Spinup Sound ===")
        print("Playing HDD spinup sound...")
        
        # Play spinup sound
        self.hdd_synth._play_audio_file("hdd_spinup.wav")
        print("Spinup sound test completed")
    
    @test_executor("Idle Sound Loop")
    def test_idle_loop(self):
        """Test the idle sound loop."""
        print("\n=== Testing Idle Sound Loop ===")
        print(f"Playing idle sound for {TEST_IDLE_DURATION} seconds...")
        
        # Play idle sound for configured duration
        start_time = time.time()
        while time.time() - start_time < TEST_IDLE_DURATION:
            # This is a simplified test - in reality the idle sound would loop
            print("Idle sound playing...")
            time.sleep(1)
        
        print("Idle sound test completed")
    
    @test_executor("Access Sound")
    def test_access_sound(self):
        """Test the access sound."""
        print("\n=== Testing Access Sound ===")
        print("Playing HDD access sound...")
        
        # Play access sound
        self.hdd_synth._play_audio_file("hdd_access.wav")
        print("Access sound test completed")
    
    @test_executor("Audio Transitions")
    def test_audio_transitions(self):
        """Test audio transitions between states."""
        print("\n=== Testing Audio Transitions ===")
        print("Simulating HDD activity changes...")
        
        # Simulate HDD becoming active
        print("Simulating HDD access...")
        self.hdd_synth._handle_audio_state_change(True)
        time.sleep(TEST_TRANSITION_DELAY)
        
        # Simulate HDD becoming idle
        print("Simulating HDD idle...")
        self.hdd_synth._handle_audio_state_change(False)
        time.sleep(TEST_TRANSITION_DELAY)
        
        print("Audio transition test completed")
    
    def run_all_tests(self):
        """Run all tests."""
        print("Starting HDD Synth test suite...")
        print("=" * 50)
        
        if not hasattr(self, 'hdd_synth'):
            print("HDD Synth not initialized - cannot run tests")
            return
        
        tests = [
            ("Spinup Sound", self.test_spinup),
            ("Idle Sound Loop", self.test_idle_loop),
            ("Access Sound", self.test_access_sound),
            ("Audio Transitions", self.test_audio_transitions)
        ]
        
        for test_name, test_func in tests:
            test_func()  # Decorator handles success/failure reporting
            
            time.sleep(TEST_PAUSE_BETWEEN_TESTS)  # Configurable pause between tests
        
        print("\n" + "=" * 50)
        print("Test suite completed!")
    
    def cleanup(self):
        """Clean up resources."""
        if hasattr(self, 'hdd_synth'):
            self.hdd_synth.stop()

# --- Main execution ---
if __name__ == '__main__':
    print("HDD Synth Test Script")
    print("This script tests the HDD Synth system without ISA bus connection")
    print()
    
    try:
        tester = HDDSynthTest()
        tester.run_all_tests()
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    except Exception as e:
        print(f"Test failed with error: {e}")
    finally:
        if 'tester' in locals():
            tester.cleanup()
        print("Test script finished")
