"""Diagnostic / interactive routines for the SD card. Not used by the main app."""
import busio
import digitalio
import storage
import os
import time

import settings


def test_spi_connection():
    print("Testing SPI connection...")
    try:
        spi = busio.SPI(
            settings.SDCARD_SCK_PIN,
            settings.SDCARD_MOSI_PIN,
            settings.SDCARD_MISO_PIN,
        )
        print("  SPI bus initialized")

        cs = digitalio.DigitalInOut(settings.SDCARD_CS_PIN)
        cs.direction = digitalio.Direction.OUTPUT
        cs.value = True
        print("  Chip select pin configured")

        return spi, cs
    except Exception as e:
        print(f"  SPI initialization failed: {e}")
        return None, None


def test_sd_card_detection(spi, cs):
    print("Testing SD card detection...")
    try:
        import adafruit_sdcard
        sd = adafruit_sdcard.SDCard(spi, cs)
        print("  SD card object created")

        cs.value = False
        time.sleep(0.001)
        cs.value = True
        print("  Basic SD card communication successful")
        return sd
    except ImportError:
        print("  adafruit_sdcard library not found")
        return None
    except Exception as e:
        print(f"  SD card detection failed: {e}")
        return None


def mount_sd_card(sd):
    try:
        vfs = storage.VfsFat(sd)
        storage.mount(vfs, settings.SDCARD_MOUNT_POINT)
        print(f"  SD card mounted at {settings.SDCARD_MOUNT_POINT}")
        return True
    except Exception as e:
        print(f"  Mounting failed: {e}")
        return False


def list_sd_card_contents():
    print("Listing SD card contents...")
    try:
        os.chdir(settings.SDCARD_MOUNT_POINT)
        items = os.listdir()

        if not items:
            print("  SD card is empty")
            return

        print(f"  Found {len(items)} item(s):")

        files = []
        directories = []
        for item in sorted(items):
            try:
                stat = os.stat(item)
                if stat[0] & 0x4000:
                    directories.append(item)
                else:
                    files.append(item)
            except OSError:
                files.append(item)

        if directories:
            print("  Directories:")
            for directory in directories:
                print(f"      {directory}/")

        if files:
            print("  Files:")
            for file in files:
                try:
                    stat = os.stat(file)
                    size = stat[6]
                    if size < 1024:
                        size_str = f"{size} B"
                    elif size < 1024 * 1024:
                        size_str = f"{size / 1024:.1f} KB"
                    else:
                        size_str = f"{size / (1024 * 1024):.1f} MB"
                    print(f"      {file:<20} ({size_str})")
                except OSError:
                    print(f"      {file:<20} (size unknown)")
    except Exception as e:
        print(f"  Error listing contents: {e}")


def test_file_operations():
    print("Testing file operations...")

    test_file = "test_write.txt"
    test_content = "CircuitPython SD card test - " + str(time.monotonic())

    try:
        with open(test_file, "w") as f:
            f.write(test_content)
        print(f"  Wrote test file: {test_file}")

        with open(test_file, "r") as f:
            read_content = f.read()

        if read_content == test_content:
            print("  File read/write test successful")
        else:
            print("  File content mismatch")

        os.remove(test_file)
        print("  Test file cleaned up")
    except Exception as e:
        print(f"  File operations test failed: {e}")


def unmount_sd_card():
    print("Unmounting SD card...")
    try:
        storage.umount(settings.SDCARD_MOUNT_POINT)
        print("  SD card unmounted successfully")
    except Exception as e:
        print(f"  Unmounting failed: {e}")


def run_sd_diagnostic():
    print("=" * 60)
    print("SD CARD DIAGNOSTIC - CircuitPython")
    print("=" * 60)

    spi, cs = test_spi_connection()
    if not spi:
        print("DIAGNOSTIC FAILED: Cannot initialize SPI")
        return

    sd = test_sd_card_detection(spi, cs)
    if not sd:
        print("DIAGNOSTIC FAILED: Cannot detect SD card")
        return

    if not mount_sd_card(sd):
        print("DIAGNOSTIC FAILED: Cannot mount SD card")
        return

    list_sd_card_contents()
    test_file_operations()
    unmount_sd_card()

    try:
        cs.deinit()
    except Exception:
        pass

    print("SD CARD DIAGNOSTIC COMPLETED SUCCESSFULLY")


if __name__ == "__main__":
    run_sd_diagnostic()
