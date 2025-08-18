"""
HDD Synth - CircuitPython Version
Monitors ISA bus for HDD activity and plays mechanical hard drive audio samples.
Based on the working CircuitPython PoC approach.
"""

import time
import board
import busio
import digitalio
import storage
import sdcard
import audiobusio
import audiocore
import audiomixer
import rp2

# Import configuration
from config import *

class HDDSynth:
    """HDD Synth system using CircuitPython audio libraries."""
    
    def __init__(self):
        """Initialize the HDD Synth system."""
        self._log("Initializing HDD Synth...")
        
        # Initialize hardware components
        self._init_pins()
        self._init_sd_card()
        self._init_audio_system()
        self._init_isa_monitoring()
        
        # Audio state
        self.last_hdd = False
        self.spinup = None
        self.idle = None
        self.access = None
        
        # HDD activity detection state (like main_mk3_debounce.py)
        self.hdd_activity_counter = 0
        self.hdd_poll_counter = 0
        self.last_activity_time = 0
        
        self._log("HDD Synth initialization complete")
    
    def _log(self, message, level="INFO"):
        """Log messages with timestamp and level."""
        timestamp = time.monotonic()
        print(f"[{timestamp:6.1f}s] {level}: {message}")
    
    def _create_digital_pin(self, pin_number, direction, pull=None, initial_value=None):
        """Helper method to create and configure a digital pin."""
        pin = digitalio.DigitalInOut(getattr(board, f"GP{pin_number}"))
        pin.direction = direction
        if pull:
            pin.pull = pull
        if initial_value is not None:
            pin.value = initial_value
        return pin
    
    def _init_pins(self):
        """Initialize GPIO pins for hardware connections."""
        self._log("Initializing GPIO pins...")
        
        # ISA Bus Monitoring Pins
        self.addr_pins = []
        for i in range(ADDR_PIN_COUNT):
            pin = self._create_digital_pin(ADDR_PIN_BASE + i, digitalio.Direction.INPUT, digitalio.Pull.UP)
            self.addr_pins.append(pin)
        
        # IOR and IOW pins
        self.ior_pin = self._create_digital_pin(IOR_PIN, digitalio.Direction.INPUT, digitalio.Pull.UP)
        self.iow_pin = self._create_digital_pin(IOW_PIN, digitalio.Direction.INPUT, digitalio.Pull.UP)
        
        # Mute pin for amplifier (start muted)
        self.mute_pin = self._create_digital_pin(MUTE_PIN, digitalio.Direction.OUTPUT, initial_value=True)
        
        self._log(f"Initialized {len(self.addr_pins)} address pins, IOR, IOW, and mute pins")
    
    def _init_sd_card(self):
        """Initialize SD card for audio file storage."""
        self._log("Initializing SD card...")
        
        try:
            # Initialize SPI for SD card
            self.spi = busio.SPI(
                clock=getattr(board, f"GP{SCK_PIN}"),
                MOSI=getattr(board, f"GP{MOSI_PIN}"),
                MISO=getattr(board, f"GP{MISO_PIN}")
            )
            
            # Initialize SD card
            self.cs = digitalio.DigitalInOut(getattr(board, f"GP{CS_PIN}"))
            self.sdcard = sdcard.SDCard(self.spi, self.cs)
            
            # Mount filesystem
            self.vfs = storage.VfsFat(self.sdcard)
            storage.mount(self.vfs, MOUNT_POINT)
            
            # List available audio files
            self._log("SD card mounted successfully")
            self._list_audio_files()
            
        except Exception as e:
            self._log(f"SD card initialization failed: {e}", "ERROR")
            raise
    
    def _list_audio_files(self):
        """List available audio files on SD card."""
        try:
            import os
            files = os.listdir(MOUNT_POINT)
            audio_files = [f for f in files if f.endswith('.wav')]
            self._log(f"Found {len(audio_files)} WAV files: {audio_files}")
        except Exception as e:
            self._log(f"Could not list audio files: {e}", "WARNING")
    
    def _init_audio_system(self):
        """Initialize CircuitPython audio system."""
        self._log("Initializing audio system...")
        
        try:
            # Initialize I2S audio output
            self.audio_out = audiobusio.I2SOut(
                bit_clock=getattr(board, f"GP{BCK_PIN}"),
                word_select=getattr(board, f"GP{WS_PIN}"),
                data=getattr(board, f"GP{SD_PIN}"),
                sample_rate=SAMPLE_RATE_HZ
            )
            
            # Create audio mixer for better control
            self.mixer = audiomixer.Mixer(
                voice_count=1,
                sample_rate=SAMPLE_RATE_HZ,
                channel_count=CHANNELS,
                bits_per_sample=BITS_PER_SAMPLE,
                samples_signed=True
            )
            
            # Attach mixer to audio output
            self.audio_out.play(self.mixer)
            
            # Load audio files
            self._load_audio_files()
            
            self._log("Audio system initialized successfully")
            
        except Exception as e:
            self._log(f"Audio system initialization failed: {e}", "ERROR")
            raise
    
    def _load_audio_files(self):
        """Load audio files from SD card."""
        self._log("Loading audio files...")
        
        try:
            # Load all audio files
            audio_files = {
                'spinup': SPINUP_FILE,
                'idle': IDLE_FILE,
                'access': ACCESS_FILE
            }
            
            for audio_type, filename in audio_files.items():
                file_path = f"{MOUNT_POINT}/{filename}"
                setattr(self, audio_type, audiocore.WaveFile(open(file_path, "rb")))
                self._log(f"Loaded {audio_type}: {filename}")
            
        except Exception as e:
            self._log(f"Failed to load audio files: {e}", "ERROR")
            raise
    
    def _create_pio_program(self, program_name, pin_index):
        """Helper method to create PIO program for ISA monitoring."""
        program = f"""
            .program {program_name}
            .side_set 1
            
            wait 0 pin {pin_index}  ; Wait for pin to go low
            in pins, {ADDR_PIN_COUNT}   ; Capture address lines
            push          ; Push to FIFO
            wait 1 pin {pin_index}  ; Wait for pin to go high
        """
        return rp2.asm_pio(program)
    
    def _create_state_machine(self, sm_id, pio_program, in_pin, freq):
        """Helper method to create and configure a PIO state machine."""
        return rp2.StateMachine(
            sm_id, pio_program, freq=freq,
            in_pins=in_pin,
            in_shiftdir=rp2.PIO.SHIFT_LEFT,
            in_autopush=True, 
            autopush_thresh=ADDR_PIN_COUNT
        )
    
    def _init_isa_monitoring(self):
        """Initialize ISA bus monitoring using PIO."""
        self._log("Initializing ISA bus monitoring...")
        
        try:
            # Create PIO programs for IOR and IOW monitoring
            self.ior_sm = self._create_pio_program("ior_monitor", 0)
            self.iow_sm = self._create_pio_program("iow_monitor", 1)
            
            # Create state machines
            self.ior_state_machine = self._create_state_machine(
                0, self.ior_sm, self.addr_pins[0], ISA_BUS_FREQ
            )
            self.iow_state_machine = self._create_state_machine(
                1, self.iow_sm, self.addr_pins[0], ISA_BUS_FREQ
            )
            
            # Start monitoring
            self.ior_state_machine.active(1)
            self.iow_state_machine.active(1)
            
            self._log("ISA bus monitoring initialized and active")
            
        except Exception as e:
            self._log(f"ISA bus monitoring initialization failed: {e}", "ERROR")
            # Fall back to simple pin monitoring
            self._log("Falling back to simple pin monitoring")
            self.ior_state_machine = None
            self.iow_state_machine = None
    
    def _is_hdd_port_address(self, address):
        """Check if an address matches HDD port addresses."""
        if address is None:
            return False
        masked_address = address & ADDRESS_BITMASK
        return masked_address in [HDD_DATA_PORT & ADDRESS_BITMASK, HDD_STATUS_PORT & ADDRESS_BITMASK]
    
    def _update_activity_counters(self, addr_value, source="PIO"):
        """Update HDD activity counters based on detected address."""
        if not self._is_hdd_port_address(addr_value):
            return
        
        current_time = time.monotonic() * 1000  # Convert to milliseconds
        
        # Reset counters if there has been no activity for a while
        if current_time - self.last_activity_time > ACTIVITY_TIMEOUT_MS:
            if self.hdd_activity_counter > 0 or self.hdd_poll_counter > 0:
                self._log(f"{source}: Activity timeout - resetting counters")
            self.hdd_activity_counter = 0
            self.hdd_poll_counter = 0
        
        self.last_activity_time = current_time
        
        # Update activity counters based on detected addresses
        if (addr_value & ADDRESS_BITMASK) == (HDD_DATA_PORT & ADDRESS_BITMASK):
            self.hdd_activity_counter += 1
            if VERBOSE_ACTIVITY_LOGGING:
                self._log(f"{source}: HDD data activity detected (count: {self.hdd_activity_counter})")
        elif (addr_value & ADDRESS_BITMASK) == (HDD_STATUS_PORT & ADDRESS_BITMASK):
            self.hdd_poll_counter += 1
            if VERBOSE_ACTIVITY_LOGGING:
                self._log(f"{source}: HDD status poll detected (count: {self.hdd_poll_counter})")
    
    def _check_activity_thresholds(self):
        """Check if activity thresholds have been exceeded and reset counters."""
        # Check if the aggregated activity has exceeded the threshold
        if self.hdd_activity_counter > ACTIVITY_THRESHOLD:
            self._log(f"HDD activity threshold exceeded ({self.hdd_activity_counter} > {ACTIVITY_THRESHOLD})")
            self.hdd_activity_counter = 0  # Reset the counter
            return True
        
        # Check if the aggregated poll activity has exceeded the threshold
        if self.hdd_poll_counter > ACTIVITY_THRESHOLD:
            self._log(f"HDD poll threshold exceeded ({self.hdd_poll_counter} > {ACTIVITY_THRESHOLD})")
            self.hdd_poll_counter = 0  # Reset the counter
            return True
        
        return False
    
    def _detect_hdd_activity_pio(self):
        """Detect HDD activity using PIO state machines with threshold-based filtering."""
        if not (self.ior_state_machine and self.iow_state_machine):
            return False
        
        # Check for data in FIFOs
        if self.ior_state_machine.rx_fifo() or self.iow_state_machine.rx_fifo():
            # Read and check if it's HDD-related
            ior_data = self.ior_state_machine.rx_fifo()
            iow_data = self.iow_state_machine.rx_fifo()
            
            # Update activity counters for both IOR and IOW data
            if ior_data:
                self._update_activity_counters(ior_data, "PIO-IOR")
            if iow_data:
                self._update_activity_counters(iow_data, "PIO-IOW")
        
        # Check if thresholds are exceeded
        return self._check_activity_thresholds()
    
    def _detect_hdd_activity_fallback(self):
        """Fallback HDD activity detection using simple pin monitoring with threshold-based filtering."""
        if self.ior_pin.value == False or self.iow_pin.value == False:
            # Check address pins for HDD port addresses
            addr_value = 0
            for i, pin in enumerate(self.addr_pins):
                if pin.value:
                    addr_value |= (1 << i)
            
            # Update activity counters
            self._update_activity_counters(addr_value, "Fallback")
            
            # Check if thresholds are exceeded
            return self._check_activity_thresholds()
        
        return False
    
    def _detect_hdd_activity(self):
        """Detect HDD activity using ISA bus monitoring."""
        try:
            # Try PIO-based detection first
            if self._detect_hdd_activity_pio():
                return True
            
            # Fall back to simple pin monitoring
            return self._detect_hdd_activity_fallback()
            
        except Exception as e:
            self._log(f"Error detecting HDD activity: {e}", "ERROR")
            return False
    
    def _play_spinup_sound(self):
        """Play the spinup sound and wait for completion."""
        self._log("Playing spinup sound...")
        self.mixer.voice[0].play(self.spinup)
        while self.mixer.voice[0].playing:
            time.sleep(SPINUP_PLAYBACK_DELAY_MS / 1000.0)
    
    def _handle_hdd_state_change(self, hdd_active):
        """Handle HDD state changes by playing appropriate audio."""
        if hdd_active:
            self._log("Access")
            self.mixer.voice[0].play(self.access)
        else:
            self._log("Idling")
            self.mixer.voice[0].play(self.idle, loop=True)
        
        # Small delay for state change
        time.sleep(HDD_STATE_CHANGE_DELAY_MS / 1000.0)
    
    def _ensure_audio_playing(self, hdd_active):
        """Ensure appropriate audio is playing based on HDD state."""
        if not self.mixer.voice[0].playing:
            if hdd_active:
                self.mixer.voice[0].play(self.access)
            else:
                self.mixer.voice[0].play(self.idle, loop=True)
    
    def _run_simulation_mode(self, count):
        """Run simulation mode to generate test HDD activity."""
        if not SIMULATION_MODE:
            return count, None
        
        count += 1
        if count > SIMULATION_INTERVAL_MS:
            import random
            rnd = random.random()
            hdd_active = rnd > (1.0 - SIMULATION_ACTIVITY_PROBABILITY)
            
            if hdd_active:
                self._log("SIMULATION: HDD activity triggered")
            else:
                self._log("SIMULATION: HDD idle")
            
            return 0, hdd_active
        
        return count, None
    
    def _run_main_loop(self):
        """Run the main monitoring and audio control loop."""
        count = 0
        
        while True:
            # Detect HDD activity
            hdd_active = self._detect_hdd_activity()
            
            # Handle simulation mode
            count, sim_hdd_active = self._run_simulation_mode(count)
            if sim_hdd_active is not None:
                hdd_active = sim_hdd_active
            
            # Handle HDD state changes
            if hdd_active != self.last_hdd:
                self._handle_hdd_state_change(hdd_active)
            
            # Ensure audio is playing
            self._ensure_audio_playing(hdd_active)
            
            # Update state and delay
            self.last_hdd = hdd_active
            time.sleep(MAIN_LOOP_DELAY_MS / 1000.0)
    
    def start(self):
        """Start the HDD Synth system using exact CircuitPython PoC logic."""
        self._log("Starting HDD Synth...")
        
        # Unmute amplifier
        self.mute_pin.value = False
        
        # Play spinup sound first
        self._play_spinup_sound()
        
        # Log startup information
        self._log("HDD Synth running - monitoring for HDD activity...")
        self._log(f"Monitoring ISA ports: 0x{HDD_DATA_PORT:03X} (data), 0x{HDD_STATUS_PORT:03X} (status)")
        if SIMULATION_MODE:
            self._log("SIMULATION MODE: ENABLED - Will generate test HDD activity every 5 seconds")
        self._log("Press Ctrl+C to stop")
        
        try:
            self._run_main_loop()
        except KeyboardInterrupt:
            self._log("Stopping HDD Synth...")
            self.stop()
    
    def stop(self):
        """Stop the HDD Synth system."""
        self._log("Stopping HDD Synth...")
        
        try:
            # Stop all audio
            if self.mixer:
                self.mixer.voice[0].stop()
            
            # Mute amplifier
            if self.mute_pin:
                self.mute_pin.value = True
            
            # Stop PIO state machines
            if hasattr(self, 'ior_state_machine') and self.ior_state_machine:
                self.ior_state_machine.active(0)
            if hasattr(self, 'iow_state_machine') and self.iow_state_machine:
                self.iow_state_machine.active(0)
            
            self._log("HDD Synth stopped")
            
        except Exception as e:
            self._log(f"Error stopping HDD Synth: {e}", "ERROR")


def main():
    """Main entry point."""
    try:
        # Validate configuration
        validate_config()
        
        # Create and start HDD Synth
        hdd_synth = HDDSynth()
        hdd_synth.start()
        
    except Exception as e:
        print(f"Fatal error: {e}")
        import sys
        sys.print_exception(e)


if __name__ == "__main__":
    main()
