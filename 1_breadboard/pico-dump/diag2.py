# audio_player.py
#
# A MicroPython script for the Raspberry Pi Pico to play a WAV file
# through a Pico Audio Pack using the I2S protocol.
#
# This script now contains a custom, Pico-compatible SD card driver
# to avoid the "ImportError: no module named 'pyb'" issue.
# The script is now a single, self-contained file.
# You must upload your WAV file to the SD card with the name 'audio.wav'.

import machine
import os
import time
from machine import I2S, Pin, SPI
import uos

# --- BEGIN: Pico-compatible SD card driver code ---
# This driver is designed specifically for the Raspberry Pi Pico
# and uses the 'machine' module. It is a more robust version of
# the previous simplified driver.

_CMD_TIMEOUT = 500
_R1_IDLE_STATE = 0x01

class SDCard:
    def __init__(self, spi, cs_pin):
        self.spi = spi
        self.cs_pin = cs_pin
        self.cs = Pin(self.cs_pin, Pin.OUT)
        self.cs.value(1)
        self.sector_size = 512
        self.capacity_in_sectors = 0
        self.size = 0

    def _wait_for_card_ready(self):
        end_time = time.ticks_ms() + 1000
        while time.ticks_diff(end_time, time.ticks_ms()) > 0:
            if self.spi.read(1)[0] == 0xff:
                return True
        return False

    def _cmd(self, cmd, arg, crc, read_timeout=None):
        self.cs.value(0)
        
        # Build the command packet
        tx_buf = bytearray([cmd | 0x40, arg >> 24, (arg >> 16) & 0xff, (arg >> 8) & 0xff, arg & 0xff, crc])
        self.spi.write(tx_buf)

        def _get_resp():
            end_time = time.ticks_ms() + _CMD_TIMEOUT
            while time.ticks_diff(end_time, time.ticks_ms()) > 0:
                resp = self.spi.read(1, 0xff)[0]
                if resp != 0xff:
                    return resp
            return 0xff
        
        resp = _get_resp()

        if cmd == 0x08:  # SEND_IF_COND (CMD8)
            resp_data = self.spi.read(4)
            return resp, resp_data
        
        elif cmd == 0x09: # SEND_CSD (CMD9)
            resp_data = bytearray(16)
            self.spi.readinto(resp_data)
            self.spi.read(2) # Read CRC
            self.cs.value(1)
            return resp, resp_data
            
        elif cmd == 0x11: # READ_SINGLE_BLOCK (CMD17)
            # Read dummy byte and data token
            self._wait_for_card_ready()
            token = self.spi.read(1)[0]
            if token != 0xfe:
                self.cs.value(1)
                raise OSError("Read failed: Data token not found")
        
        self.cs.value(1)
        return resp

    def init_card(self):
        """
        Initializes the SD card by sending a sequence of commands.
        """
        print("  -> Initializing SD card...")
        self.cs.value(1)
        self.spi.init(baudrate=100000, polarity=0, phase=0)
        
        for _ in range(10): # Send 80 clocks
            self.spi.write(b'\xff')

        # CMD0: GO_IDLE_STATE
        resp = self._cmd(0, 0, 0x95)
        if resp != _R1_IDLE_STATE:
            raise OSError("No SD card found")
        
        # CMD8: SEND_IF_COND
        resp, resp_data = self._cmd(8, 0x1aa, 0x87)
        if resp == _R1_IDLE_STATE and resp_data[2:4] != b'\x01\xaa':
            raise OSError("SD card not compatible")

        # ACMD41 with HCS (Host Capacity Support)
        max_attempts = 200
        for i in range(max_attempts):
            resp = self._cmd(55, 0, 0x65)
            if resp != _R1_IDLE_STATE:
                time.sleep_ms(10)
                continue
            
            resp = self._cmd(41, 0x40000000, 0x77)
            if resp == 0:
                break
        else:
            raise OSError("SD card failed to initialize with CMD41")

        # CMD58: READ_OCR
        self._cmd(58, 0, 0xfd)
        
        self.spi.init(baudrate=10000000, polarity=0, phase=0) # High speed
        
        # CMD9: SEND_CSD to determine capacity
        resp, csd_data = self._cmd(9, 0, 0)
        if resp == 0:
            csd_structure = (csd_data[0] >> 6)
            if csd_structure == 0:
                c_size = ((csd_data[6] & 0b11) << 10 | csd_data[7] << 2 | csd_data[8] >> 6)
                c_size_mult = ((csd_data[9] & 0b11) << 1 | csd_data[10] >> 7)
                self.capacity_in_sectors = (c_size + 1) * (2 ** (c_size_mult + 2)) * (2 ** (csd_data[5] & 0b1111)) // 512
            else: # CSD V2.0 (High Capacity)
                c_size = (csd_data[7] & 0b111111) << 16 | csd_data[8] << 8 | csd_data[9]
                self.capacity_in_sectors = (c_size + 1) * 1024
        else:
            raise OSError("Could not read CSD")

    def __len__(self):
        return self.capacity_in_sectors

    def readblocks(self, block_num, buf):
        resp = self._cmd(17, block_num * 512, 0)
        
        if resp == 0:
            self.spi.readinto(buf)
            self.spi.read(2) # Read CRC
        else:
            raise OSError("Read failed")

    def writeblocks(self, block_num, buf):
        resp = self._cmd(24, block_num * 512, 0)
        if resp == 0:
            self.spi.write(b'\xfe')
            self.spi.write(buf)
            self.spi.write(b'\xff\xff') # CRC
        else:
            raise OSError("Write failed")

# --- END: SD card driver code ---


# --- Pin Definitions for Pico Audio Pack ---
BCK_PIN = machine.Pin(26, machine.Pin.OUT) # Bit Clock (SCK)
WS_PIN = machine.Pin(27, machine.Pin.OUT)  # Word Select (WS)
SD_PIN = machine.Pin(28, machine.Pin.OUT)  # Serial Data (SD)
MUTE_PIN = machine.Pin(22, machine.Pin.OUT) # Mute pin for the amplifier

# --- Pin Definitions for SD Card Reader (SPI) ---
SCK_PIN = Pin(14)  # SPI Clock
MOSI_PIN = Pin(15) # SPI Master Out, Slave In
MISO_PIN = Pin(12) # SPI Master In, Slave Out
CS_PIN = Pin(13)   # Chip Select for the SD card

# --- Configuration Constants ---
SAMPLE_RATE_HZ = 16000
BITS_PER_SAMPLE = 16
CHANNELS = I2S.STEREO
BUFFER_SIZE = 512
SD_MOUNT_POINT = '/sd'

def diagnose_sd_card_pins():
    """
    A simple diagnostic function to test if the SD card is responding to
    a basic command (CMD0) to check for correct wiring.
    """
    print("Running diagnostic check for SD card wiring...")
    try:
        spi = SPI(1, sck=SCK_PIN, mosi=MOSI_PIN, miso=MISO_PIN)
        cs = Pin(CS_PIN, Pin.OUT, value=1)
        
        # Send 80 clocks to put the card in SPI mode.
        spi.init(baudrate=100000, polarity=0, phase=0)
        for _ in range(10):
            spi.write(b'\xff')

        # Send CMD0: GO_IDLE_STATE
        cs.value(0)
        tx_buf = bytearray([0x40, 0, 0, 0, 0, 0x95])
        spi.write(tx_buf)

        # Look for a response (should be 0x01 for IDLE_STATE)
        end_time = time.ticks_ms() + 200
        resp = 0xff
        while time.ticks_diff(end_time, time.ticks_ms()) > 0:
            resp = spi.read(1, 0xff)[0]
            if resp != 0xff:
                break
        
        cs.value(1)
        
        if resp == 0x01:
            print("✅ Diagnostic Passed: SD card is responding to initial command.")
            print("This indicates your SCK, MOSI, and MISO pins are likely correct.")
            return True
        else:
            print(f"❌ Diagnostic Failed: SD card did not respond. Response was: 0x{resp:02x}")
            print("This suggests a wiring issue with SCK, MOSI, MISO, or CS.")
            return False
            
    except Exception as e:
        print(f"An unexpected error occurred during diagnosis: {e}")
        return False

def mount_sd_card():
    """
    Initializes the SPI bus and mounts the SD card file system.
    Returns True on success, False on failure.
    """
    print("Attempting to mount SD card...")
    try:
        # Initialize the SPI bus for the SD card reader.
        # This will be used by the external sdcard driver.
        spi = machine.SPI(1, sck=SCK_PIN, mosi=MOSI_PIN, miso=MISO_PIN)
        
        # Create an instance of our new, robust SD card driver.
        sd = SDCard(spi, CS_PIN)
        
        # Mount the SD card at the specified path.
        uos.mount(sd, SD_MOUNT_POINT)
        print("SD card mounted successfully.")
        return True
    except OSError as e:
        print(f"Error mounting SD card: {e}")
        print("Please check your wiring, power supply, and card format.")
        return False

def play_audio(filename='audio.wav'):
    """
    Plays a WAV file from the SD card.
    The script checks if the file exists and unmutes the amplifier.
    """
    audio_path = f"{SD_MOUNT_POINT}/{filename}"
    
    print(f"Initializing audio playback from {audio_path}...")

    try:
        # We need to check for the file's existence after mounting the card.
        if filename not in uos.listdir(SD_MOUNT_POINT):
            print(f"Error: The file '{filename}' was not found on the SD card.")
            return

        with open(audio_path, 'rb') as audio_file:
            header = audio_file.read(44)
            print("WAV header skipped.")

            audio_out = I2S(
                0,
                sck=BCK_PIN,
                ws=WS_PIN,
                sd=SD_PIN,
                mode=I2S.TX,
                bits=BITS_PER_SAMPLE,
                format=CHANNELS,
                rate=SAMPLE_RATE_HZ,
                ibuf=BUFFER_SIZE
            )

            MUTE_PIN.value(0)
            print("Amplifier unmuted.")

            num_bytes_written = 0
            while True:
                audio_data = audio_file.read(BUFFER_SIZE)
                if not audio_data:
                    break
                num_bytes_written += audio_out.write(audio_data)

            MUTE_PIN.value(1)
            print("Amplifier muted.")

            audio_out.deinit()
            print("Audio playback finished.")

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        uos.umount(SD_MOUNT_POINT)
        print("SD card unmounted.")

# --- Main execution ---
if __name__ == '__main__':
    MUTE_PIN.value(1)
    
    time.sleep(1)
    
    if diagnose_sd_card_pins():
        if mount_sd_card():
            play_audio()

    print("Script execution complete.")
