"""
SD Card Diagnostic Script for CircuitPython
Tests SD card connectivity and lists all files on the card.
"""

import board
import busio
import digitalio
import storage
import os
import time

# SD Card pin configuration (SPI)
SCK_PIN = 14    # SPI Clock
MOSI_PIN = 15   # SPI MOSI  
MISO_PIN = 12   # SPI MISO
CS_PIN = 13     # SPI Chip Select

# Mount point for the SD card
MOUNT_POINT = '/sd'

def test_spi_connection():
    """Test basic SPI communication."""
    print("🔌 Testing SPI connection...")
    
    try:
        # Initialize SPI bus using board pin objects
        spi = busio.SPI(
            getattr(board, f"GP{SCK_PIN}"),   # SCK
            getattr(board, f"GP{MOSI_PIN}"),  # MOSI
            getattr(board, f"GP{MISO_PIN}")   # MISO
        )
        print("  ✅ SPI bus initialized")
        
        # Initialize chip select pin
        cs = digitalio.DigitalInOut(getattr(board, f"GP{CS_PIN}"))
        cs.direction = digitalio.Direction.OUTPUT
        cs.value = True  # Start with CS high (inactive)
        print("  ✅ Chip select pin configured")
        
        return spi, cs
        
    except Exception as e:
        print(f"  ❌ SPI initialization failed: {e}")
        return None, None

def test_sd_card_detection(spi, cs):
    """Test if SD card responds to basic commands."""
    print("\n💾 Testing SD card detection...")
    
    try:
        # Try to import the SD card library
        try:
            import adafruit_sdcard
            print("  ✅ adafruit_sdcard library available")
        except ImportError:
            print("  ❌ adafruit_sdcard library not found")
            print("     Install with: pip install adafruit-circuitpython-sdcard")
            return None
            
        # Create SD card object
        sd = adafruit_sdcard.SDCard(spi, cs)
        print("  ✅ SD card object created")
        
        # Test basic communication
        cs.value = False  # Activate chip select
        time.sleep(0.001)  # Small delay
        cs.value = True   # Deactivate chip select
        print("  ✅ Basic SD card communication successful")
        
        return sd
        
    except Exception as e:
        print(f"  ❌ SD card detection failed: {e}")
        return None

def mount_sd_card(sd):
    """Mount the SD card filesystem."""
    print("\n📁 Mounting SD card filesystem...")
    
    try:
        # Create a filesystem object
        vfs = storage.VfsFat(sd)
        print("  ✅ VFS filesystem created")
        
        # Mount the filesystem
        storage.mount(vfs, MOUNT_POINT)
        print(f"  ✅ SD card mounted at {MOUNT_POINT}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Mounting failed: {e}")
        return False

def list_sd_card_contents():
    """List all files and directories on the SD card."""
    print("\n📋 Listing SD card contents...")
    
    try:
        # Change to the SD card directory
        os.chdir(MOUNT_POINT)
        print(f"  ✅ Changed to {MOUNT_POINT}")
        
        # List all files and directories
        items = os.listdir()
        
        if not items:
            print("  ⚠️  SD card is empty (no files or directories)")
            return
            
        print(f"  📁 Found {len(items)} item(s):")
        print("  " + "=" * 50)
        
        # Categorize and display items
        files = []
        directories = []
        
        for item in sorted(items):
            try:
                # Get item info
                stat = os.stat(item)
                if stat[0] & 0x4000:  # Directory
                    directories.append(item)
                else:  # File
                    files.append(item)
            except OSError:
                # If we can't stat it, assume it's a file
                files.append(item)
        
        # Display directories first
        if directories:
            print("  📁 Directories:")
            for directory in directories:
                print(f"      {directory}/")
            print()
        
        # Display files with sizes
        if files:
            print("  📄 Files:")
            for file in files:
                try:
                    stat = os.stat(file)
                    size = stat[6]  # File size
                    if size < 1024:
                        size_str = f"{size} B"
                    elif size < 1024 * 1024:
                        size_str = f"{size / 1024:.1f} KB"
                    else:
                        size_str = f"{size / (1024 * 1024):.1f} MB"
                    print(f"      {file:<20} ({size_str})")
                except OSError:
                    print(f"      {file:<20} (size unknown)")
        
        print("  " + "=" * 50)
        
    except Exception as e:
        print(f"  ❌ Error listing contents: {e}")

def test_file_operations():
    """Test basic file read/write operations."""
    print("\n✏️  Testing file operations...")
    
    test_file = "test_write.txt"
    test_content = "CircuitPython SD card test - " + str(time.monotonic())
    
    try:
        # Test writing a file
        with open(test_file, "w") as f:
            f.write(test_content)
        print(f"  ✅ Wrote test file: {test_file}")
        
        # Test reading the file
        with open(test_file, "r") as f:
            read_content = f.read()
        
        if read_content == test_content:
            print("  ✅ File read/write test successful")
        else:
            print("  ❌ File content mismatch")
            
        # Clean up test file
        os.remove(test_file)
        print("  ✅ Test file cleaned up")
        
    except Exception as e:
        print(f"  ❌ File operations test failed: {e}")

def unmount_sd_card():
    """Unmount the SD card."""
    print("\n🔌 Unmounting SD card...")
    
    try:
        storage.umount(MOUNT_POINT)
        print("  ✅ SD card unmounted successfully")
    except Exception as e:
        print(f"  ❌ Unmounting failed: {e}")

def run_sd_diagnostic():
    """Run the complete SD card diagnostic."""
    print("=" * 60)
    print("🔍 SD CARD DIAGNOSTIC - CircuitPython")
    print("=" * 60)
    
    # Test 1: SPI connection
    spi, cs = test_spi_connection()
    if not spi:
        print("\n❌ DIAGNOSTIC FAILED: Cannot initialize SPI")
        return
    
    # Test 2: SD card detection
    sd = test_sd_card_detection(spi, cs)
    if not sd:
        print("\n❌ DIAGNOSTIC FAILED: Cannot detect SD card")
        return
    
    # Test 3: Mount filesystem
    if not mount_sd_card(sd):
        print("\n❌ DIAGNOSTIC FAILED: Cannot mount SD card")
        return
    
    # Test 4: List contents
    list_sd_card_contents()
    
    # Test 5: File operations
    test_file_operations()
    
    # Test 6: Unmount
    unmount_sd_card()
    
    # Clean up
    try:
        cs.deinit()
        print("  ✅ Chip select pin cleaned up")
    except:
        pass
    
    print("\n" + "=" * 60)
    print("✅ SD CARD DIAGNOSTIC COMPLETED SUCCESSFULLY")
    print("=" * 60)

if __name__ == "__main__":
    run_sd_diagnostic()
