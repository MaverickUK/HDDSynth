"""
HDDSynth - Main Application
Orchestrates ISA bus monitoring, audio playback, and simulation mode.
"""

import time
import random
import board
import digitalio

# Import our modules
from config import *
from isa import ISAMonitor
from sdcard import SDCardManager
from audio import AudioManager

class HDDSynth:
    """Main HDDSynth application class."""
    
    def __init__(self):
        """Initialize HDDSynth with all components."""
        print("=" * 60)
        print("🚀 HDDSYNTH INITIALIZING")
        print("=" * 60)
        
        # Validate configuration
        validate_config()
        
        # Initialize components
        self.sd_card = SDCardManager(config)
        self.audio = AudioManager(config)
        self.isa_monitor = ISAMonitor(config)
        
        # State tracking
        self.hdd_active = False
        self.last_hdd_state = False
        self.simulation_counter = 0
        
        # Onboard LED for status
        self.led = digitalio.DigitalInOut(board.LED)
        self.led.direction = digitalio.Direction.OUTPUT
        self.led.value = False
        
        print("✅ HDDSynth initialization completed")
    
    def startup_sequence(self):
        """Run the startup sequence: load audio files and play spinup sound."""
        print("\n🎵 Starting audio sequence...")
        
        # Load required audio files
        if not self.sd_card.load_required_audio_files():
            print("❌ Failed to load required audio files")
            return False
        
        # Play spinup sound
        spinup_file = self.sd_card.get_audio_file('spinup')
        if not spinup_file:
            print("❌ Spinup audio file not available")
            return False
        
        print("🔄 Playing HDD spinup sound...")
        if not self.audio.play_spinup_sound(spinup_file):
            print("❌ Failed to play spinup sound")
            return False
        
        print("✅ Startup sequence completed")
        return True
    
    def start_idle_loop(self):
        """Start the idle sound loop."""
        idle_file = self.sd_card.get_audio_file('idle')
        if not idle_file:
            print("❌ Idle audio file not available")
            return False
        
        print("🔄 Starting idle sound loop...")
        return self.audio.play_idle_sound(idle_file)
    
    def handle_hdd_activity_change(self):
        """Handle changes in HDD activity state."""
        if self.hdd_active != self.last_hdd_state:
            print(f"💾 HDD activity changed: {'Active' if self.hdd_active else 'Idle'}")
            
            if self.hdd_active:
                # HDD became active - play access sound
                access_file = self.sd_card.get_audio_file('access')
                if access_file:
                    self.audio.play_access_sound(access_file)
                else:
                    print("❌ Access audio file not available")
            else:
                # HDD became idle - resume idle loop
                idle_file = self.sd_card.get_audio_file('idle')
                if idle_file:
                    self.audio.resume_idle_sound(idle_file)
                else:
                    print("❌ Idle audio file not available")
            
            # Update state
            self.last_hdd_state = self.hdd_active
            
            # Small delay to prevent rapid state changes
            time.sleep(self.config.HDD_STATE_CHANGE_DELAY_MS / 1000.0)
    
    def simulate_hdd_activity(self):
        """Simulate HDD activity for testing without ISA bus connection."""
        self.simulation_counter += 1
        
        if self.simulation_counter >= 5000:  # Simulate every ~5 seconds
            # Random HDD activity based on probability
            if random.random() > (1.0 - self.config.SIMULATION_ACTIVITY_PROBABILITY):
                self.hdd_active = True
            else:
                self.hdd_active = False
            
            self.simulation_counter = 0
    
    def detect_real_hdd_activity(self):
        """Detect real HDD activity from ISA bus monitoring."""
        self.hdd_active = self.isa_monitor.detect_hdd_activity()
    
    def update_led_status(self):
        """Update onboard LED to show HDD activity status."""
        self.led.value = self.hdd_active
    
    def main_loop(self):
        """Main application loop."""
        print("\n🔄 Starting main loop...")
        print("Press Ctrl+C to stop")
        
        try:
            while True:
                # Detect HDD activity (real or simulated)
                if self.config.SIMULATION_MODE:
                    self.simulate_hdd_activity()
                else:
                    self.detect_real_hdd_activity()
                
                # Handle state changes
                self.handle_hdd_activity_change()
                
                # Update status indicators
                self.update_led_status()
                
                # Small delay to prevent excessive CPU usage
                time.sleep(self.config.MAIN_LOOP_DELAY_MS / 1000.0)
                
        except KeyboardInterrupt:
            print("\n⏹️  Stopping HDDSynth...")
        except Exception as e:
            print(f"\n❌ Error in main loop: {e}")
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Clean up all resources."""
        print("\n🧹 Cleaning up resources...")
        
        # Stop audio
        self.audio.stop_audio()
        
        # Clean up components
        self.audio.cleanup()
        self.isa_monitor.cleanup()
        self.sd_card.cleanup()
        
        # Turn off LED
        if self.led:
            self.led.value = False
            self.led.deinit()
        
        print("✅ Cleanup completed")
    
    def run(self):
        """Run the complete HDDSynth application."""
        try:
            # Run startup sequence
            if not self.startup_sequence():
                print("❌ Startup failed, exiting")
                return
            
            # Start idle loop
            if not self.start_idle_loop():
                print("❌ Failed to start idle loop, exiting")
                return
            
            # Run main loop
            self.main_loop()
            
        except Exception as e:
            print(f"❌ Fatal error: {e}")
            self.cleanup()

def main():
    """Main entry point."""
    # Create and run HDDSynth
    hdd_synth = HDDSynth()
    hdd_synth.run()

if __name__ == "__main__":
    main()
