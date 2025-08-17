import machine
import os
import time

# Import the SDCard driver
import sdcard

# Define the pin connections for the SD card reader
SCK_PIN = machine.Pin(14)
MOSI_PIN = machine.Pin(15)
MISO_PIN = machine.Pin(12)
CS_PIN = machine.Pin(13)

# Define the mount point for the SD card
MOUNT_POINT = '/sd'

def run_sd_diagnostic():
    """
    Initializes SPI, creates an SDCard block device, and lists its contents.
    """
    print("--- SD Card Diagnostic Script ---")
    
    # Initialize the SPI bus
    spi = machine.SPI(1, 
                      baudrate=1000000, 
                      polarity=0, 
                      phase=0, 
                      sck=SCK_PIN, 
                      mosi=MOSI_PIN, 
                      miso=MISO_PIN)
    
    # Create an SD card block device object
    try:
        sd = sdcard.SDCard(spi, CS_PIN)
        print("✅ SD card block device initialized.")
    except Exception as e:
        print(f"❌ Error initializing SD card block device: {e}")
        return

    try:
        # Attempt to mount the SD card filesystem
        os.mount(sd, MOUNT_POINT)
        print("✅ SD card successfully mounted.")
        
        # Change to the SD card directory to list files
        os.chdir(MOUNT_POINT)
        files = os.listdir()
        
        if files:
            print(f"\n📁 Files found on the SD card ({len(files)} total):")
            for file in files:
                print(f"   - {file}")
        else:
            print("\n⚠️ The SD card is empty. No files found.")
            
    except OSError as e:
        # Handle specific mounting errors
        if e.args[0] == 19:  # errno.ENODEV
            print("❌ Error: SD card not detected. Check connections or card insertion.")
        elif e.args[0] == 5: # errno.EIO
            print("❌ Error: I/O error during communication. Check wiring and card format.")
        else:
            print(f"❌ An error occurred: {e}")
            
    finally:
        # Unmount the SD card to free up resources
        try:
            os.umount(MOUNT_POINT)
            print("\nSD card unmounted.")
        except OSError:
            pass # SD card was not mounted, so nothing to unmount
            
# Run the diagnostic script
if __name__ == "__main__":
    run_sd_diagnostic()