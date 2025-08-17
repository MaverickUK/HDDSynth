# HDD Synth - Quick Start Guide

## What You Need

### Hardware
- [ ] Raspberry Pi Pico
- [ ] Pico Audio Pack
- [ ] SD Card Module (SPI)
- [ ] ISA Prototyping Board
- [ ] MicroSD Card (FAT32 formatted)
- [ ] Audio samples (WAV files)
- [ ] 2 x TXS0108E level shifter (Convert 5v ISA signals to 3.3v Pico)
- [ ] Prototyping ISA board

### Software
- [ ] MicroPython firmware on Pico
- [ ] `sdcard.py` library
- [ ] HDD Synth files

## Setup

### Step 0: Aquire prototype ISA PCB
Contains the TXS level shifters connected to the ISA address bus, IOR and IOW lines

### Step 1: Prepare Your Pico
1. Download MicroPython firmware: https://micropython.org/download/rp2-pico/
2. Hold BOOTSEL button and plug in Pico
3. Copy firmware to Pico (it will appear as USB drive)
4. Pico will restart with MicroPython

### Step 2: Install Dependencies
1. Download `sdcard.py` from: https://github.com/micropython/micropython/tree/master/drivers/sdcard
2. Copy to Pico's `lib/` folder (create if it doesn't exist)

### Step 3: Prepare Audio Files
1. Format SD card as FAT32
2. Copy these WAV files to root directory:
   - `hdd_spinup.wav`
   - `hdd_idle.wav`
   - `hdd_access.wav`
3. Insert SD card into module

### Step 4: Wire Up Hardware
Connect according to this pin map:

| Component | Pico GPIO | Signal |
|-----------|-----------|---------|
| ISA A0-A9 | GPIO 0-9  | Address bus |
| ISA IOR   | GPIO 10   | I/O Read |
| ISA IOW   | GPIO 11   | I/O Write |
| SD SCK    | GPIO 14   | SPI Clock |
| SD MOSI   | GPIO 15   | SPI MOSI |
| SD MISO   | GPIO 12   | SPI MISO |
| SD CS     | GPIO 13   | SPI CS |
| Audio BCK | GPIO 26   | Bit Clock |
| Audio WS  | GPIO 27   | Word Select |
| Audio SD  | GPIO 28   | Serial Data |
| Audio MUTE| GPIO 22   | Mute control |

### Step 5: Upload Code
1. Copy `main.py` to Pico
2. Copy `config.py` to Pico
3. The system will auto-start with `main.py`

### Step 6: Test
1. Power on your Pico
2. You should hear the HDD spinup sound
3. Then idle sound will loop continuously
4. When you access files on your PC, you should hear access sounds

## Troubleshooting

### No Audio Output
- Check Pico Audio Pack connections
- Verify MUTE pin is connected to GPIO 22
- Ensure audio files are 16kHz, 16-bit, stereo WAV

### SD Card Not Found
- Check SPI connections (SCK, MOSI, MISO, CS)
- Verify SD card is FAT32 formatted
- Ensure audio files are in root directory

### ISA Bus Not Detected
- Verify all address pins (A0-A9) are connected
- Check IOR and IOW connections
- Ensure ISA board is properly seated

### Audio Cuts Out
- Check power supply (Pico needs stable 5V)
- Verify SD card is high-speed (Class 10+)
- Reduce audio buffer size in config if needed

## Customization

### Change Audio Files
1. Replace WAV files on SD card
2. Update filenames in `config.py`
3. Ensure new files match format requirements

### Adjust Pin Assignments
1. Edit `config.py`
2. Modify pin numbers as needed
3. Restart Pico

### Tune Detection Sensitivity
1. Adjust `ACTIVITY_THRESHOLD` in config
2. Modify `ACTIVITY_TIMEOUT_MS` for response speed
3. Test with your specific hardware

## Need Help?

- Check the main README.md for detailed information
- Review pin connections carefully
- Test with `test.py` first
- Ensure all hardware is properly connected

## Success!

Once working, your HDD Synth will:
- ✅ Play spinup sound on power-up
- ✅ Loop idle sound when no activity
- ✅ Play access sounds during HDD operations
- ✅ Respond in real-time to ISA bus activity
- ✅ Work as a plug-and-play ISA card

Enjoy your authentic mechanical HDD sounds! 🎵
