import busio
import sdcardio
import storage

import settings
import beep


def _test_spi_connection():
    """Initialise the SPI bus. Returns spi or None."""
    print("Testing SPI connection...")

    try:
        spi = busio.SPI(
            settings.SDCARD_SCK_PIN,
            settings.SDCARD_MOSI_PIN,
            settings.SDCARD_MISO_PIN,
        )
        print("  SPI bus initialized")
        return spi

    except Exception as e:
        print(f"  SPI initialization failed: {e}")
        return None


def _test_sd_card_detection(spi):
    """Probe the SD card. Returns the SDCard object or None."""
    print("Testing SD card detection...")

    try:
        sd = sdcardio.SDCard(spi, settings.SDCARD_CS_PIN, baudrate=settings.SDCARD_BAUDRATE)
        print("  SD card detected")
        return sd

    except Exception as e:
        print(f"  SD card detection failed: {e}")
        return None


def _mount_sd_card(sd):
    """Mount the SD card filesystem at SDCARD_MOUNT_POINT."""
    print("Mounting SD card filesystem...")

    try:
        vfs = storage.VfsFat(sd)
        storage.mount(vfs, settings.SDCARD_MOUNT_POINT)
        print(f"  SD card mounted at {settings.SDCARD_MOUNT_POINT}")
        return True
    except Exception as e:
        print(f"  Mounting failed: {e}")
        return False


def initialise(mixer=None):
    """Bring the SD card up. Returns True if successful, False otherwise.
    Beeps NO_SD_CARD on failure when a mixer is given."""
    spi = _test_spi_connection()
    if not spi:
        print("SD init failed: cannot initialize SPI")
        return False

    sd = _test_sd_card_detection(spi)
    if not sd:
        print("SD init failed: cannot detect SD card")
        return False

    if not _mount_sd_card(sd):
        print("SD init failed: cannot mount SD card")
        return False

    return True
