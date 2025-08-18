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
        self.audio = None
        self.spinup = None
        self.idle = None
        self.access = None
        
        self._log("HDD Synth initialization complete")
    
    def _log(self, message, level="INFO"):
        """Log messages with timestamp and level."""
        timestamp = time.monotonic()
        print(f"[{timestamp:6.1f}s] {level}: {message}")
    
    def _init_pins(self):
        """Initialize GPIO pins for hardware connections."""
        self._log("Initializing GPIO pins...")
        
        # ISA Bus Monitoring Pins
        self.addr_pins = []
        for i in range(ADDR_PIN_COUNT):
            pin = digitalio.DigitalInOut(getattr(board, f"GP{ADDR_PIN_BASE + i}"))
            pin.direction = digitalio.Direction.INPUT
            pin.pull = digitalio.Pull.UP
            self.addr_pins.append(pin)
        
        self.ior_pin = digitalio.DigitalInOut(getattr(board, f"GP{IOR_PIN}"))
        self.ior_pin.direction = digitalio.Direction.INPUT
        self.ior_pin.pull = digitalio.Pull.UP
        
        self.iow_pin = digitalio.DigitalInOut(getattr(board, f"GP{IOW_PIN}"))
        self.iow_pin.direction = digitalio.Direction.INPUT
        self.iow_pin.pull = digitalio.Pull.UP
        
        # Mute pin for amplifier
        self.mute_pin = digitalio.DigitalInOut(getattr(board, f"GP{MUTE_PIN}"))
        self.mute_pin.direction = digitalio.Direction.OUTPUT
        self.mute_pin.value = True  # Start muted
        
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
            # Load spinup sound
            self.spinup = audiocore.WaveFile(open(f"{MOUNT_POINT}/{SPINUP_FILE}", "rb"))
            self._log(f"Loaded spinup: {SPINUP_FILE}")
            
            # Load idle sound (will be looped)
            self.idle = audiocore.WaveFile(open(f"{MOUNT_POINT}/{IDLE_FILE}", "rb"))
            self._log(f"Loaded idle: {IDLE_FILE}")
            
            # Load access sound
            self.access = audiocore.WaveFile(open(f"{MOUNT_POINT}/{ACCESS_FILE}", "rb"))
            self._log(f"Loaded access: {ACCESS_FILE}")
            
        except Exception as e:
            self._log(f"Failed to load audio files: {e}", "ERROR")
            raise
    
    def _init_isa_monitoring(self):
        """Initialize ISA bus monitoring using PIO."""
        self._log("Initializing ISA bus monitoring...")
        
        # PIO program for IOR monitoring (read operations)
        ior_program = """
            .program ior_monitor
            .side_set 1
            
            wait 0 pin 0  ; Wait for IOR to go low
            in pins, 10   ; Capture 10 address lines
            push          ; Push to FIFO
            wait 1 pin 0  ; Wait for IOR to go high
        """
        
        # PIO program for IOW monitoring (write operations)
        iow_program = """
            .program iow_monitor
            .side_set 1
            
            wait 0 pin 1  ; Wait for IOW to go low
            in pins, 10   ; Capture 10 address lines
            push          ; Push to FIFO
            wait 1 pin 1  ; Wait for IOW to go high
        """
        
        try:
            # Initialize IOR state machine
            self.ior_sm = rp2.asm_pio(ior_program)
            self.ior_state_machine = rp2.StateMachine(
                0, self.ior_sm, freq=ISA_BUS_FREQ, 
                in_pins=self.addr_pins[0],  # Base address pin
                in_shiftdir=rp2.PIO.SHIFT_LEFT,
                in_autopush=True, autopush_thresh=10
            )
            
            # Initialize IOW state machine
            self.iow_sm = rp2.asm_pio(iow_program)
            self.iow_state_machine = rp2.StateMachine(
                1, self.iow_sm, freq=ISA_BUS_FREQ,
                in_pins=self.addr_pins[0],  # Base address pin
                in_shiftdir=rp2.PIO.SHIFT_LEFT,
                in_autopush=True, autopush_thresh=10
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
    
    def _detect_hdd_activity(self):
        """Detect HDD activity using ISA bus monitoring."""
        try:
            # Check if PIO state machines are available
            if self.ior_state_machine and self.iow_state_machine:
                # Check for data in FIFOs
                if self.ior_state_machine.rx_fifo() or self.iow_state_machine.rx_fifo():
                    # Read and check if it's HDD-related
                    ior_data = self.ior_state_machine.rx_fifo()
                    iow_data = self.iow_state_machine.rx_fifo()
                    
                    # Check if address matches HDD ports
                    if ior_data and (ior_data & 0xFF) in [HDD_DATA_PORT & 0xFF, HDD_STATUS_PORT & 0xFF]:
                        return True
                    if iow_data and (iow_data & 0xFF) in [HDD_DATA_PORT & 0xFF, HDD_STATUS_PORT & 0xFF]:
                        return True
            
            # Fallback: simple pin monitoring
            if self.ior_pin.value == False or self.iow_pin.value == False:
                # Check address pins for HDD port addresses
                addr_value = 0
                for i, pin in enumerate(self.addr_pins):
                    if pin.value:
                        addr_value |= (1 << i)
                
                # Check if address matches HDD ports
                if (addr_value & 0xFF) in [HDD_DATA_PORT & 0xFF, HDD_STATUS_PORT & 0xFF]:
                    return True
            
            return False
            
        except Exception as e:
            self._log(f"Error detecting HDD activity: {e}", "ERROR")
            return False
    
    def start(self):
        """Start the HDD Synth system using exact CircuitPython PoC logic."""
        self._log("Starting HDD Synth...")
        self._log("Playing spinup sound...")
        
        # Unmute amplifier
        self.mute_pin.value = False
        
        # Play spinup sound first (blocking)
        self.mixer.voice[0].play(self.spinup)
        while self.mixer.voice[0].playing:
            time.sleep(SPINUP_PLAYBACK_DELAY_MS / 1000.0)
        
        # Remember the previous HDD access value (like CircuitPython PoC)
        last_hdd = False
        hdd_active = False
        
        self._log("HDD Synth running - monitoring for HDD activity...")
        self._log(f"Monitoring ISA ports: 0x{HDD_DATA_PORT:03X} (data), 0x{HDD_STATUS_PORT:03X} (status)")
        if SIMULATION_MODE:
            self._log("SIMULATION MODE: ENABLED - Will generate test HDD activity every 5 seconds")
        self._log("Press Ctrl+C to stop")
        
        try:
            # Simple counter-based simulation exactly like CircuitPython PoC
            count = 0
            
            while True:
                # Detect HDD activity
                hdd_active = self._detect_hdd_activity()
                
                # Simulation mode: generate random HDD activity for testing (exactly like CircuitPython PoC)
                if SIMULATION_MODE:
                    count = count + 1
                    if count > SIMULATION_INTERVAL_MS:  # Every ~5 seconds (5000 * 1ms delay)
                        import random
                        rnd = random.random()
                        if rnd > (1.0 - SIMULATION_ACTIVITY_PROBABILITY):  # Configurable chance of HDD activity
                            hdd_active = True
                            self._log("SIMULATION: HDD activity triggered")
                        else:
                            hdd_active = False
                            self._log("SIMULATION: HDD idle")
                        count = 0
                
                # Start playing sample on HDD activity change (exactly like CircuitPython PoC)
                if hdd_active != self.last_hdd:
                    if hdd_active:
                        self._log("Access")
                        self.mixer.voice[0].play(self.access)
                        time.sleep(HDD_STATE_CHANGE_DELAY_MS / 1000.0)  # HDD_STATE_CHANGE_DELAY
                    else:
                        self._log("Idling")
                        self.mixer.voice[0].play(self.idle, loop=True)
                        time.sleep(HDD_STATE_CHANGE_DELAY_MS / 1000.0)  # HDD_STATE_CHANGE_DELAY
                
                # Loop sample if stopped (exactly like CircuitPython PoC)
                if not self.mixer.voice[0].playing:
                    if hdd_active:
                        self.mixer.voice[0].play(self.access)
                    else:
                        self.mixer.voice[0].play(self.idle, loop=True)
                
                self.last_hdd = hdd_active
                
                # Small delay like CircuitPython PoC
                time.sleep(MAIN_LOOP_DELAY_MS / 1000.0)
                
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
