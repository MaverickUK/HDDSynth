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
        
        try:
            # Initialize SPI bus
            self.spi = SPI(1,
                          baudrate=1000000,
                          polarity=0,
                          phase=0,
                          sck=SCK_PIN_OBJ,
                          mosi=MOSI_PIN_OBJ,
                          miso=MISO_PIN_OBJ)
            
            # Create SD card block device
            self.sd = sdcard.SDCard(self.spi, CS_PIN_OBJ)
            
            # Mount SD card
            os.mount(self.sd, MOUNT_POINT)
            os.chdir(MOUNT_POINT)
            
            # List available files
            files = os.listdir()
            self._log(f"SD card mounted. Found {len(files)} files:")
            for file in files:
                self._log(f"  - {file}")
                
        except Exception as e:
            self._log(f"Error initializing SD card: {e}", "ERROR")
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
        required_files = [SPINUP_FILE, IDLE_FILE, ACCESS_FILE]
        
        for file in required_files:
            if file not in os.listdir():
                self._log(f"Warning: Required audio file '{file}' not found on SD card", "WARN")
            else:
                self._log(f"Audio file '{file}' found")
    
    def _play_audio_file(self, filename, loop=False):
        """Play an audio file from the SD card."""
        if not self.audio_out:
            return
        
        try:
            # Stop current playback
            if self.is_playing:
                self.audio_out.deinit()
                self.audio_out = self._create_i2s_output()
            
            # Unmute amplifier
            MUTE_PIN_OBJ.value(0)
            
            # Open and play audio file
            with open(filename, 'rb') as audio_file:
                # Skip WAV header (44 bytes)
                audio_file.read(44)
                
                # Read and play audio data
                while True:
                    audio_data = audio_file.read(BUFFER_SIZE)
                    if not audio_data:
                        if loop:
                            # Loop: seek back to start of audio data
                            audio_file.seek(44)
                            continue
                        else:
                            break
                    
                    self.audio_out.write(audio_data)
            
            # Mute amplifier
            MUTE_PIN_OBJ.value(1)
            
        except Exception as e:
            self._log(f"Error playing audio file {filename}: {e}", "ERROR")
            MUTE_PIN_OBJ.value(1)
    
    def _detect_hdd_activity(self):
        """Detect HDD activity from ISA bus monitoring."""
        current_time = time.ticks_ms()
        hdd_activity = False
        
        # Check IOR state machine
        if self.sm_ior.rx_fifo() > 0:
            addr = self.sm_ior.get()
            if addr in [HDD_DATA_PORT, HDD_STATUS_PORT]:
                self.last_activity_time = current_time
                hdd_activity = True
        
        # Check IOW state machine
        if self.sm_iow.rx_fifo() > 0:
            addr = self.sm_iow.get()
            if addr in [HDD_DATA_PORT, HDD_STATUS_PORT]:
                self.last_activity_time = current_time
                hdd_activity = True
        
        # Check for activity timeout
        if time.ticks_diff(current_time, self.last_activity_time) > ACTIVITY_TIMEOUT_MS:
            hdd_activity = False
        
        return hdd_activity
    
    def _handle_audio_state_change(self, hdd_active):
        """Handle audio state changes based on HDD activity."""
        if hdd_active != self.hdd_active:
            self.hdd_active = hdd_active
            
            if hdd_active:
                self._log("HDD Access detected - playing access sound")
                # Play access sound (will be interrupted when access stops)
                self._play_audio_file(ACCESS_FILE, loop=True)
            else:
                self._log("HDD idle - playing idle sound")
                # Play idle sound in loop
                self._play_audio_file(IDLE_FILE, loop=True)
    
    def start(self):
        """Start the HDD Synth system."""
        self._log("Starting HDD Synth...")
        self._log("Playing spinup sound...")
        
        # Play spinup sound first
        self._play_audio_file(SPINUP_FILE)
        
        self._log("HDD Synth running - monitoring for HDD activity...")
        self._log("Press Ctrl+C to stop")
        
        try:
            while True:
                # Detect HDD activity
                hdd_active = self._detect_hdd_activity()
                
                # Handle audio state changes
                self._handle_audio_state_change(hdd_active)
                
                # Small delay to prevent excessive CPU usage
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
