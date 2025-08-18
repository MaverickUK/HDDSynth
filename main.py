# main.py
# HDD Synth - A MicroPython program for the Raspberry Pi Pico
# to monitor ISA bus HDD activity and play corresponding audio samples
# through a Pico Audio Pack using files stored on an SD card.
#
# NOTE: This file imports all configuration from config.py
#       Modify pin assignments and settings in the config file, not here.

import rp2
from machine import Pin, I2S, SPI
import os
import time
import sdcard

# Import configuration - all settings come from config.py
from config import *
from config import SIMULATION_MODE

# --- PIO Program Definitions ---
@rp2.asm_pio(
    in_shiftdir=rp2.PIO.SHIFT_LEFT,
    autopush=True,
    push_thresh=10,
    fifo_join=rp2.PIO.JOIN_RX
)
def ior_pio_program():
    """PIO program for detecting I/O Read (IOR) activity."""
    wrap_target()
    wait(0, pin, 0)        # Wait for IOR pin to go low (active low)
    in_(pins, 10)          # Read 10 address pins (A0-A9)
    wrap()

@rp2.asm_pio(
    in_shiftdir=rp2.PIO.SHIFT_LEFT,
    autopush=True,
    push_thresh=10,
    fifo_join=rp2.PIO.JOIN_RX
)
def iow_pio_program():
    """PIO program for detecting I/O Write (IOW) activity."""
    wrap_target()
    wait(0, pin, 0)        # Wait for IOW pin to go low (active low)
    in_(pins, 10)          # Read 10 address pins (A0-A9)
    wrap()

class HDDSynth:
    def __init__(self):
        """Initialize the HDD Synth system."""
        self.audio_out = None
        self.current_audio_file = None
        self.is_playing = False
        self.hdd_active = False
        self.last_activity_time = time.ticks_ms()
        
        # Initialize hardware
        self._init_isa_monitoring()
        self._init_sd_card()
        self._init_audio()
        
        # Load audio files
        self._load_audio_files()
        
        self._log("HDD Synth initialized successfully!")
    
    def _log(self, message, level="INFO"):
        """Log messages with consistent formatting."""
        timestamp = time.ticks_ms()
        print(f"[{level}] {timestamp}ms: {message}")
    
    def _init_isa_monitoring(self):
        """Initialize ISA bus monitoring with PIO."""
        self._log("Initializing ISA bus monitoring...")
        
        # Configure address pins as inputs with pull-up resistors
        self.addr_pins = [Pin(i, Pin.IN, Pin.PULL_UP) for i in range(ADDR_PIN_COUNT)]
        
        # Configure control pins
        self.ior_pin = Pin(IOR_PIN, Pin.IN, Pin.PULL_UP)
        self.iow_pin = Pin(IOW_PIN, Pin.IN, Pin.PULL_UP)
        
        # Create and configure state machines
        self.sm_ior = self._create_state_machine(0, ior_pio_program, self.ior_pin)
        self.sm_iow = self._create_state_machine(1, iow_pio_program, self.iow_pin)
        
        # Start state machines
        self.sm_ior.active(1)
        self.sm_iow.active(1)
        
        self._log("ISA bus monitoring active")
    
    def _create_state_machine(self, sm_id, program, jmp_pin):
        """Create and configure a PIO state machine for ISA bus monitoring."""
        return rp2.StateMachine(
            sm_id, program,
            freq=ISA_BUS_FREQ,
            in_base=Pin(ADDR_PIN_BASE),
            jmp_pin=jmp_pin
        )
    
    def _init_sd_card(self):
        """Initialize SD card for audio file storage."""
        self._log("Initializing SD card...")
        
        max_retries = 3
        retry_delay = 1  # seconds
        
        for attempt in range(max_retries):
            try:
                self._log(f"SD card initialization attempt {attempt + 1}/{max_retries}")
                
                # Initialize SPI bus with detailed logging
                self._log(f"Creating SPI bus with pins: SCK={SCK_PIN}, MOSI={MOSI_PIN}, MISO={MISO_PIN}, CS={CS_PIN}")
                self.spi = SPI(1,
                              baudrate=1000000,
                              polarity=0,
                              phase=0,
                              sck=SCK_PIN_OBJ,
                              mosi=MOSI_PIN_OBJ,
                              miso=MISO_PIN_OBJ)
                self._log("SPI bus created successfully")
                
                # Create SD card block device
                self._log("Creating SD card block device...")
                self.sd = sdcard.SDCard(self.spi, CS_PIN_OBJ)
                self._log("SD card block device created successfully")
                
                # Mount SD card
                self._log(f"Mounting SD card to {MOUNT_POINT}...")
                os.mount(self.sd, MOUNT_POINT)
                self._log("SD card mounted successfully")
                
                # Change to SD card directory
                self._log("Changing to SD card directory...")
                os.chdir(MOUNT_POINT)
                self._log(f"Current working directory: {os.getcwd()}")
                
                # List available files with detailed info
                self._log("Reading SD card contents...")
                files = os.listdir()
                self._log(f"SD card mounted. Found {len(files)} files:")
                
                # Log each file with size and type info
                for file in files:
                    try:
                        stat_info = os.stat(file)
                        file_size = stat_info[6]  # File size in bytes
                        self._log(f"  - {file} ({file_size} bytes)")
                    except Exception as e:
                        self._log(f"  - {file} (error reading stats: {e})")
                
                # Verify required audio files exist
                self._log("Verifying required audio files...")
                required_files = [SPINUP_FILE, IDLE_FILE, ACCESS_FILE]
                for file in required_files:
                    if file in files:
                        self._log(f"  ✅ {file} found")
                    else:
                        self._log(f"  ❌ {file} NOT FOUND", "WARN")
                
                # If we get here, initialization was successful
                self._log("SD card initialization completed successfully")
                return
                    
            except Exception as e:
                self._log(f"Error initializing SD card (attempt {attempt + 1}): {e}", "ERROR")
                self._log(f"Error type: {type(e).__name__}", "ERROR")
                self._log(f"Error details: {str(e)}", "ERROR")
                
                # Try to clean up on failure
                try:
                    if hasattr(self, 'sd'):
                        self._log("Attempting to unmount SD card...")
                        os.umount(MOUNT_POINT)
                except:
                    pass
                
                if attempt < max_retries - 1:
                    self._log(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                else:
                    self._log("Maximum retries reached, giving up", "ERROR")
                    raise
    
    def _create_i2s_output(self):
        """Create and configure I2S audio output."""
        return I2S(
            0,                          # I2S bus number
            sck=BCK_PIN_OBJ,
            ws=WS_PIN_OBJ,
            sd=SD_PIN_OBJ,
            mode=I2S_TX,                # Transmit mode
            bits=BITS_PER_SAMPLE,       # 16-bit data
            format=I2S_STEREO,          # Stereo
            rate=SAMPLE_RATE_HZ,        # Audio sample rate
            ibuf=BUFFER_SIZE            # Internal buffer size
        )
    
    def _init_audio(self):
        """Initialize audio output system."""
        self._log("Initializing audio system...")
        
        # Initially mute amplifier
        MUTE_PIN_OBJ.value(1)
        
        # Create I2S audio output
        self.audio_out = self._create_i2s_output()
        
        self._log("Audio system initialized")
    
    def _load_audio_files(self):
        """Verify audio files exist on SD card."""
        self._log("Loading and verifying audio files...")
        required_files = [SPINUP_FILE, IDLE_FILE, ACCESS_FILE]
        
        # Get current directory and list files
        current_dir = os.getcwd()
        self._log(f"Current working directory: {current_dir}")
        
        try:
            available_files = os.listdir()
            self._log(f"Files available in current directory: {len(available_files)}")
            
            for file in required_files:
                if file in available_files:
                    try:
                        # Get file info
                        stat_info = os.stat(file)
                        file_size = stat_info[6]
                        self._log(f"✅ Audio file '{file}' found ({file_size} bytes)")
                        
                        # Try to open file to verify it's readable
                        with open(file, 'rb') as test_file:
                            header = test_file.read(44)  # Read WAV header
                            if len(header) == 44:
                                self._log(f"  File '{file}' is readable and has valid WAV header")
                            else:
                                self._log(f"  Warning: File '{file}' may be corrupted (header size: {len(header)})", "WARN")
                    except Exception as e:
                        self._log(f"  Error reading file '{file}': {e}", "ERROR")
                else:
                    self._log(f"❌ Required audio file '{file}' NOT FOUND on SD card", "WARN")
                    self._log(f"  Available files: {', '.join(available_files)}", "WARN")
                    
        except Exception as e:
            self._log(f"Error listing directory contents: {e}", "ERROR")
            raise
    
    def _play_audio_file(self, filename, loop=False):
        """Play an audio file from the SD card (non-blocking like CircuitPython PoC)."""
        if not self.audio_out:
            self._log("No audio output available", "ERROR")
            return
        
        self._log(f"Starting audio file: {filename}")
        
        try:
            # Verify file exists before attempting to play
            if filename not in os.listdir():
                self._log(f"File '{filename}' not found in current directory", "ERROR")
                return
            
            # Stop current playback
            if self.is_playing:
                self._log("Stopping current audio playback")
                self.audio_out.deinit()
                self.audio_out = self._create_i2s_output()
            
            # Set playing state
            self.is_playing = True
            self.current_audio_file = filename
            
            # Unmute amplifier
            MUTE_PIN_OBJ.value(0)
            self._log("Amplifier unmuted, starting playback")
            
            # Start playback in background (non-blocking)
            # This is a simplified approach - in a real implementation you'd use threading
            # For now, we'll use a timer-based approach to simulate non-blocking behavior
            
            # Store file info for background playback
            self.audio_file = filename
            self.audio_loop = loop
            self.audio_position = 44  # Skip WAV header
            self.audio_file_size = os.stat(filename)[6]
            
            # Start background playback timer
            self.audio_timer = time.ticks_ms()
            
        except Exception as e:
            self._log(f"Error starting audio file '{filename}': {e}", "ERROR")
            self.is_playing = False
            self.current_audio_file = None
    
    def _update_audio_playback(self):
        """Update audio playback in background (called from main loop)."""
        if not self.is_playing or not hasattr(self, 'audio_file'):
            return
        
        # Check if it's time to read more audio data
        current_time = time.ticks_ms()
        if time.ticks_diff(current_time, self.audio_timer) < 10:  # Every 10ms
            return
        
        try:
            with open(self.audio_file, 'rb') as audio_file:
                # Seek to current position
                audio_file.seek(self.audio_position)
                
                # Read a chunk of audio data
                audio_data = audio_file.read(BUFFER_SIZE)
                if not audio_data:
                    if self.audio_loop:
                        # Loop: seek back to start of audio data
                        self.audio_position = 44
                        self._log("Looping audio file")
                    else:
                        # End of file
                        self.is_playing = False
                        self.current_audio_file = None
                        MUTE_PIN_OBJ.value(1)  # Mute amplifier
                        self._log("Audio playback completed")
                        return
                else:
                    # Write audio data to I2S
                    self.audio_out.write(audio_data)
                    self.audio_position += len(audio_data)
                
                # Update timer
                self.audio_timer = current_time
                
        except Exception as e:
            self._log(f"Error updating audio playback: {e}", "ERROR")
            self.is_playing = False
            self.current_audio_file = None
    
    def _detect_hdd_activity(self):
        """Detect HDD activity using a working approach based on CircuitPython PoC."""
        current_time = time.ticks_ms()
        hdd_activity = False
        
        # First, let's try the ISA bus monitoring (but with better debugging)
        try:
            # Check IOR state machine
            if self.sm_ior.rx_fifo() > 0:
                addr = self.sm_ior.get()
                self._log(f"IOR activity detected: 0x{addr:03X}")
                if addr in [HDD_DATA_PORT, HDD_STATUS_PORT]:
                    self.last_activity_time = current_time
                    hdd_activity = True
                    self._log(f"HDD IOR activity: 0x{addr:03X}")
            
            # Check IOW state machine
            if self.sm_iow.rx_fifo() > 0:
                addr = self.sm_iow.get()
                self._log(f"IOW activity detected: 0x{addr:03X}")
                if addr in [HDD_STATUS_PORT, HDD_DATA_PORT]:
                    self.last_activity_time = current_time
                    hdd_activity = True
                    self._log(f"HDD IOW activity: 0x{addr:03X}")
                    
        except Exception as e:
            self._log(f"Error in ISA monitoring: {e}", "ERROR")
        
        # Check for activity timeout
        if time.ticks_diff(current_time, self.last_activity_time) > ACTIVITY_TIMEOUT_MS:
            if self.hdd_active:  # Only log when state actually changes
                self._log(f"HDD activity timeout after {ACTIVITY_TIMEOUT_MS}ms")
            hdd_activity = False
        
        return hdd_activity
    
    def _handle_audio_state_change(self, hdd_active):
        """Handle audio state changes based on HDD activity (using proven CircuitPython approach)."""
        if hdd_active != self.hdd_active:
            self._log(f"HDD activity state changing from {self.hdd_active} to {hdd_active}")
            self.hdd_active = hdd_active
            
            if hdd_active:
                self._log("HDD Access detected - playing access sound")
                # Stop current audio and play access sound (will loop until HDD stops)
                if self.is_playing:
                    self._log("Stopping current audio playback")
                    self.audio_out.deinit()
                    self.audio_out = self._create_i2s_output()
                    self.is_playing = False
                    self.current_audio_file = None
                
                # Play access sound (will loop until HDD activity stops)
                self._play_audio_file(ACCESS_FILE, loop=True)
                
                # Small delay to prevent rapid state changes (like in CircuitPython)
                time.sleep_ms(50)
            else:
                self._log("HDD idle - playing idle sound")
                # Stop current audio and play idle sound in loop
                if self.is_playing:
                    self._log("Stopping current audio playback")
                    self.audio_out.deinit()
                    self.audio_out = self._create_i2s_output()
                    self.is_playing = False
                    self.current_audio_file = None
                
                # Play idle sound in loop
                self._play_audio_file(IDLE_FILE, loop=True)
                
                # Small delay to prevent rapid state changes (like in CircuitPython)
                time.sleep_ms(50)
        
        # Handle initial state (when no audio is playing yet)
        elif not self.is_playing and not hdd_active:
            self._log("Initial state - starting idle audio")
            self._play_audio_file(IDLE_FILE, loop=True)
    
    def _check_and_restart_audio(self):
        """Check if audio has stopped and restart it (using proven CircuitPython approach)."""
        if not self.is_playing:
            if self.hdd_active:
                self._log("Restarting access audio")
                self._play_audio_file(ACCESS_FILE, loop=True)
            else:
                self._log("Restarting idle audio")
                self._play_audio_file(IDLE_FILE, loop=True)
    
    def start(self):
        """Start the HDD Synth system using non-blocking audio like CircuitPython PoC."""
        self._log("Starting HDD Synth...")
        self._log("Playing spinup sound...")
        
        # Play spinup sound first (blocking - this is OK for startup)
        self._play_audio_file(SPINUP_FILE)
        
        # Remember the previous HDD access value (like CircuitPython PoC)
        last_hdd = False
        hdd_active = False
        
        self._log("HDD Synth running - monitoring for HDD activity...")
        self._log(f"Monitoring ISA ports: 0x{HDD_DATA_PORT:03X} (data), 0x{HDD_STATUS_PORT:03X} (status)")
        self._log(f"Activity timeout: {ACTIVITY_TIMEOUT_MS}ms")
        if SIMULATION_MODE:
            self._log("SIMULATION MODE: ENABLED - Will generate test HDD activity every 5 seconds")
        self._log("Press Ctrl+C to stop")
        
        try:
            # Simple counter-based simulation exactly like CircuitPython PoC
            count = 0
            
            # Start idle audio immediately (non-blocking)
            self._play_audio_file(IDLE_FILE)
            
            while True:
                # Detect HDD activity
                hdd_active = self._detect_hdd_activity()
                
                # Simulation mode: generate random HDD activity for testing (exactly like CircuitPython PoC)
                if SIMULATION_MODE:
                    count = count + 1
                    if count > 5000:  # Every ~5 seconds (5000 * 1ms delay)
                        import random
                        rnd = random.random()
                        if rnd > 0.3:  # 70% chance of HDD activity
                            hdd_active = True
                            self._log("SIMULATION: HDD activity triggered")
                        else:
                            hdd_active = False
                            self._log("SIMULATION: HDD idle")
                        count = 0
                
                # Start playing sample on HDD activity change (exactly like CircuitPython PoC)
                if hdd_active != last_hdd:
                    if hdd_active:
                        self._log("Access")
                        self._play_audio_file(ACCESS_FILE)
                        time.sleep_ms(50)  # HDD_STATE_CHANGE_DELAY = 0.05s
                    else:
                        self._log("Idling")
                        self._play_audio_file(IDLE_FILE)
                        time.sleep_ms(50)  # HDD_STATE_CHANGE_DELAY = 0.05s
                
                # Loop sample if stopped (exactly like CircuitPython PoC)
                if not self.is_playing:
                    if hdd_active:
                        self._play_audio_file(ACCESS_FILE)
                    else:
                        self._play_audio_file(IDLE_FILE)
                
                # Update audio playback in background (non-blocking)
                self._update_audio_playback()
                
                last_hdd = hdd_active
                
                # Small delay to prevent overwhelming the system
                time.sleep_ms(1)
                
        except KeyboardInterrupt:
            self._log("Stopping HDD Synth...")
            self.stop()
    
    def stop(self):
        """Stop the HDD Synth system."""
        self._log("Stopping HDD Synth...")
        
        # Mute amplifier
        MUTE_PIN_OBJ.value(1)
        
        # Stop state machines
        if hasattr(self, 'sm_ior'):
            self.sm_ior.active(0)
        if hasattr(self, 'sm_iow'):
            self.sm_iow.active(0)
        
        # Deinitialize audio
        if self.audio_out:
            self.audio_out.deinit()
        
        # Unmount SD card
        try:
            os.umount(MOUNT_POINT)
        except:
            pass
        
        self._log("HDD Synth stopped")

# --- Main execution ---
if __name__ == '__main__':
    try:
        hdd_synth = HDDSynth()
        hdd_synth.start()
    except Exception as e:
        print(f"Fatal error: {e}")
        # Ensure amplifier is muted on error
        MUTE_PIN_OBJ.value(1)
