"""
SD Card Management Module for HDDSynth
Handles SD card initialization and audio file loading.
"""

import board
import busio
import digitalio
import storage
import os
import time

class SDCardManager:
    """Manages SD card operations and audio file access."""
    
    def __init__(self, config):
        """Initialize SD card manager with configuration."""
        self.config = config
        self.spi = None
        self.cs = None
        self.sd = None
        self.vfs = None
        self.mounted = False
        self.audio_files = {}
        
        # Initialize SD card
        self._init_sd_card()
    
    def _init_sd_card(self):
        """Initialize SD card connection and mount filesystem."""
        try:
            # Initialize SPI bus
            self.spi = busio.SPI(
                getattr(board, f"GP{self.config.SCK_PIN}"),
                getattr(board, f"GP{self.config.MOSI_PIN}"),
                getattr(board, f"GP{self.config.MISO_PIN}")
            )
            print("✅ SPI bus initialized")
            
            # Initialize chip select pin
            self.cs = digitalio.DigitalInOut(getattr(board, f"GP{self.config.CS_PIN}"))
            self.cs.direction = digitalio.Direction.OUTPUT
            self.cs.value = True  # Start with CS high (inactive)
            print("✅ Chip select pin configured")
            
            # Try to import and use SD card library
            try:
                import adafruit_sdcard
                print("✅ adafruit_sdcard library available")
            except ImportError:
                print("❌ adafruit_sdcard library not found")
                print("   Install with: pip install adafruit-circuitpython-sdcard")
                return
            
            # Create SD card object
            self.sd = adafruit_sdcard.SDCard(self.spi, self.cs)
            print("✅ SD card object created")
            
            # Create and mount filesystem
            self.vfs = storage.VfsFat(self.sd)
            storage.mount(self.vfs, self.config.MOUNT_POINT)
            self.mounted = True
            print(f"✅ SD card mounted at {self.config.MOUNT_POINT}")
            
            # List available files
            self._list_available_files()
            
        except Exception as e:
            print(f"❌ SD card initialization failed: {e}")
            self.mounted = False
    
    def _list_available_files(self):
        """List all files available on the SD card."""
        if not self.mounted:
            return
        
        try:
            # Change to SD card directory
            os.chdir(self.config.MOUNT_POINT)
            
            # List all files
            files = os.listdir()
            wav_files = [f for f in files if f.endswith('.wav')]
            
            print(f"📁 Found {len(files)} total files, {len(wav_files)} WAV files")
            
            if wav_files:
                print("🎵 Available WAV files:")
                for wav_file in sorted(wav_files):
                    try:
                        stat = os.stat(wav_file)
                        size = stat[6]  # File size
                        if size < 1024:
                            size_str = f"{size} B"
                        elif size < 1024 * 1024:
                            size_str = f"{size / 1024:.1f} KB"
                        else:
                            size_str = f"{size / (1024 * 1024):.1f} MB"
                        print(f"   • {wav_file:<25} ({size_str})")
                    except OSError:
                        print(f"   • {wav_file:<25} (size unknown)")
            
        except Exception as e:
            print(f"⚠️  Error listing files: {e}")
    
    def load_audio_file(self, filename):
        """Load an audio file from the SD card."""
        if not self.mounted:
            print(f"❌ Cannot load {filename}: SD card not mounted")
            return None
        
        try:
            # Change to SD card directory
            os.chdir(self.config.MOUNT_POINT)
            
            # Check if file exists
            if filename not in os.listdir():
                print(f"❌ Audio file not found: {filename}")
                return None
            
            # Open and return file object
            file_obj = open(filename, "rb")
            print(f"✅ Loaded audio file: {filename}")
            return file_obj
            
        except Exception as e:
            print(f"❌ Error loading {filename}: {e}")
            return None
    
    def load_required_audio_files(self):
        """Load all required audio files for HDDSynth operation."""
        required_files = {
            'spinup': self.config.SPINUP_FILE,
            'idle': self.config.IDLE_FILE,
            'access': self.config.ACCESS_FILE
        }
        
        print("\n🎵 Loading required audio files...")
        
        for audio_type, filename in required_files.items():
            file_obj = self.load_audio_file(filename)
            if file_obj:
                self.audio_files[audio_type] = file_obj
            else:
                print(f"❌ Failed to load required file: {filename}")
                return False
        
        print(f"✅ All {len(self.audio_files)} audio files loaded successfully")
        return True
    
    def get_audio_file(self, audio_type):
        """Get a loaded audio file by type."""
        return self.audio_files.get(audio_type)
    
    def is_mounted(self):
        """Check if SD card is mounted."""
        return self.mounted
    
    def cleanup(self):
        """Clean up SD card resources."""
        try:
            if self.mounted and self.vfs:
                storage.umount(self.config.MOUNT_POINT)
                print("✅ SD card unmounted")
                self.mounted = False
            
            if self.cs:
                self.cs.deinit()
                print("✅ Chip select pin cleaned up")
                
        except Exception as e:
            print(f"⚠️  Error during cleanup: {e}")
