# audio_player.py
#
# A MicroPython script for the Raspberry Pi Pico to play a WAV file
# through a Pico Audio Pack using the I2S protocol.
#
# This script is designed for a 16-bit, 16kHz, stereo WAV file
# and now reads the file from an SD card.
# You must upload your WAV file to the SD card with the name 'audio.wav'.

import machine
import os
import time
from machine import I2S, Pin, SPI
import uos

# --- BEGIN: Pi Pico-compatible SD card driver code ---
#
# Source: https://github.com/micropython/micropython-lib/blob/master/micropython/drivers/storage/sdcard/sdcard.py

# Driver for SD Card, based on original by P. W. (https://github.com/peterhinch/micropython-microsd)
# which was modified by S. M. (https://github.com/sci-m) for use with the RP2040.
# This code is now included directly in the main script for convenience.

_CMD_TIMEOUT = 100
_R1_IDLE_STATE = 0x01
_R1_ILLEGAL_COMMAND = 0x05

class SDCard:
    def __init__(self, spi, cs):
        self.spi = spi
        self.cs = cs
        self.cs.init(cs.OUT, value=1)
        self.buf = bytearray(4)
        self.readblocks = self.readblocks_raw
        self.writeblocks = self.writeblocks_raw

    def _write(self, val):
        self.spi.write(self.buf, val)

    def _read(self, n):
        self.spi.read(self.buf, n)
        return self.buf

    def _cmd(self, cmd, arg, crc, read_timeout=None):
        self.cs.value(0)
        
        self.buf[0] = cmd | 0x40
        self.buf[1] = arg >> 24
        self.buf[2] = (arg >> 16) & 0xff
        self.buf[3] = (arg >> 8) & 0xff
        self.buf[4] = arg & 0xff
        self.buf[5] = crc
        
        self.spi.write(self.buf, self.buf[:6])

        def _get_resp():
            end_time = time.ticks_ms() + _CMD_TIMEOUT
            while time.ticks_diff(end_time, time.ticks_ms()) > 0:
                resp = self.spi.read(1)[0]
                if resp != 0xff:
                    return resp
            return 0xff
        
        resp = _get_resp()
        
        if cmd == 0x09: # SEND_CSD
            # CSD is 16 bytes followed by a 16-bit CRC
            response_data = self.spi.read(16)
            self.cs.value(1)
            return resp, response_data

        if cmd == 0x0d: # SEND_STATUS
            # R2 response is 2 bytes
            resp = self.spi.read(2)[0]
            self.cs.value(1)
            return resp

        if cmd == 0x11: # READ_SINGLE_BLOCK
            # Data response is 512 bytes
            self.spi.read(1) # Read dummy byte
            self.cs.value(1)
            return resp

        if cmd == 0x18: # READ_MULTIPLE_BLOCK
            # Data response is 512 bytes for each block
            self.spi.read(1) # Read dummy byte
            self.cs.value(1)
            return resp
        
        # for other commands, just return the response
        self.cs.value(1)
        return resp

    def _wait_for_card_ready(self):
        end_time = time.ticks_ms() + 500
        while time.ticks_diff(end_time, time.ticks_ms()) > 0:
            if self.spi.read(1)[0] == 0xff:
                break

    def init_card(self):
        time.sleep_ms(10)
        self.cs.value(1)
        self.spi.init(baudrate=100000, polarity=0, phase=0)
        
        for _ in range(10):
            self.spi.write(b'\xff')

        # CMD0: GO_IDLE_STATE
        self.cs.value(0)
        resp = self._cmd(0, 0, 0x95)
        if resp != _R1_IDLE_STATE:
            self.cs.value(1)
            raise OSError("No SD card found")
        
        # CMD8: SEND_IF_COND
        resp = self._cmd(8, 0x1aa, 0x87)
        if resp == _R1_IDLE_STATE:
            # Check for version 2.0
            if self.spi.read(4) != b'\x00\x00\x01\xaa':
                raise OSError("SD card not compatible")
        
        # CMD55, ACMD41
        while self._cmd(55, 0, 0x65) != _R1_IDLE_STATE:
            pass
        
        while self._cmd(41, 0x40000000, 0x77) != 0:
            pass

        # CMD58: READ_OCR
        self._cmd(58, 0, 0xfd)
        
        self.spi.init(baudrate=10000000, polarity=0, phase=0) # High speed
        
        # Get CSD to determine size
        resp, csd_data = self._cmd(9, 0, 0x65)
        if resp == 0:
            self.csd = csd_data
            self.sector_size = 512
            self.capacity_in_sectors = ((csd_data[8] << 8 | csd_data[9]) + 1) * 1024
            self.size = self.capacity_in_sectors * self.sector_size
        else:
            raise OSError("Could not read CSD")

    def readblocks_raw(self, block_num, buf):
        # We assume 512 byte blocks
        # CMD17: READ_SINGLE_BLOCK
        resp = self._cmd(17, block_num * 512, 0)
        
        if resp == 0:
            self._wait_for_card_ready()
            
            # Read data
            data_token = self.spi.read(1)[0]
            if data_token != 0xfe:
                raise OSError("Read failed")
            
            self.spi.read(len(buf), buf)
            self.spi.read(2) # Read CRC
        else:
            raise OSError("Read failed")

    def writeblocks_raw(self, block_num, buf):
        # We assume 512 byte blocks
        # CMD24: WRITE_SINGLE_BLOCK
        resp = self._cmd(24, block_num * 512, 0)

        if resp == 0:
            self._wait_for_card_ready()
            
            # Write data token and data
            self.spi.write(b'\xfe')
            self.spi.write(buf)
            self.spi.write(b'\xff\xff') # CRC

            # Wait for finish token
            end_time = time.ticks_ms() + 1000
            while time.ticks_diff(end_time, time.ticks_ms()) > 0:
                resp = self.spi.read(1)[0]
                if resp == 0:
                    break
        else:
            raise OSError("Write failed")

# --- END: Pi Pico-compatible SD card driver code ---


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

def mount_sd_card():
    """
    Initializes the SPI bus and mounts the SD card file system.
    Returns True on success, False on failure.
    """
    print("Attempting to mount SD card...")
    try:
        # Initialize the SPI bus for the SD card reader.
        # The SPI bus ID is 1 on the Pi Pico, which corresponds to pins 10-15.
        spi = SPI(1, sck=SCK_PIN, mosi=MOSI_PIN, miso=MISO_PIN)
        
        # Create an instance of the SDCard driver.
        sd = SDCard(spi, CS_PIN)
        
        # Mount the SD card at the specified path.
        uos.mount(sd, SD_MOUNT_POINT)
        print("SD card mounted successfully.")
        return True
    except OSError as e:
        print(f"Error mounting SD card: {e}")
        return False

def play_audio(filename='audio.wav'):
    """
    Plays a WAV file from the SD card.
    The script checks if the file exists and unmutes the amplifier.
    """
    audio_path = f"{SD_MOUNT_POINT}/{filename}"
    
    print(f"Initializing audio playback from {audio_path}...")

    try:
        if audio_path not in uos.listdir(SD_MOUNT_POINT):
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
    
    if mount_sd_card():
        play_audio()

    print("Script execution complete.")
