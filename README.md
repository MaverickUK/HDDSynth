## HDD Synth
<div style="background: white; display: inline-block; padding: 8px;">
  <img src="images/HDDSynthLogoSmall.png" alt="Logo">
</div>

### Recreates the sound of mechanical spinning HDDs on retro PCs that use a solid state drive.

Inspired by seeing the HDD Clicker project and wanting to more faithfully recreate the sound of old mechanical hard drives spinning up and accessing data. Because the hard drive sounds come from samples, it's possible to replace them with any hard drive recording you'd like or something completely different!

**HDD Synth now features direct ISA bus monitoring for plug-and-play operation!** After advice from [Ian Scott](https://picog.us/), the system can detect HDD activity directly from the ISA bus, eliminating the need for HDD LED connections.

Using this approach should make it very simple to also detect floppy drive access. This would mean this card could also be used by systems with a solid state floppy drive, like the GoTek.

## Features

- **Direct ISA Bus Monitoring**: Monitors ISA address bus (A0-A9) and control signals (IOR/IOW) for HDD activity
- **Real-time Audio Response**: Plays appropriate sounds based on HDD state (spinup, idle, access)
- **SD Card Storage**: Audio samples stored on removable SD card for easy customization
- **Pico Audio Pack Support**: High-quality audio output through the Pico Audio Pack
- **Configurable**: Easy-to-modify configuration file for different hardware setups

## Hardware Requirements

### Core Components
- **Raspberry Pi Pico** (RP2040)
- **Pico Audio Pack** for audio output
- **SD Card Module** (SPI interface)
- **ISA Prototyping Board** (e.g., Marten Electric ISA prototyping board)

### Pin Connections

#### ISA Bus Monitoring
| Signal | Pico GPIO | Description |
|--------|-----------|-------------|
| A0     | GPIO 0    | ISA Address Bus A0 |
| A1     | GPIO 1    | ISA Address Bus A1 |
| A2     | GPIO 2    | ISA Address Bus A2 |
| A3     | GPIO 3    | ISA Address Bus A3 |
| A4     | GPIO 4    | ISA Address Bus A4 |
| A5     | GPIO 5    | ISA Address Bus A5 |
| A6     | GPIO 6    | ISA Address Bus A6 |
| A7     | GPIO 7    | ISA Address Bus A7 |
| A8     | GPIO 8    | ISA Address Bus A8 |
| A9     | GPIO 9    | ISA Address Bus A9 |
| IOR    | GPIO 10   | ISA I/O Read signal |
| IOW    | GPIO 11   | ISA I/O Write signal |

#### SD Card (SPI)
| Signal | Pico GPIO | Description |
|--------|-----------|-------------|
| SCK    | GPIO 14   | SPI Clock |
| MOSI   | GPIO 15   | SPI MOSI |
| MISO   | GPIO 12   | SPI MISO |
| CS     | GPIO 13   | SPI Chip Select |

#### Audio Output (Pico Audio Pack)
| Signal | Pico GPIO | Description |
|--------|-----------|-------------|
| BCK    | GPIO 26   | Bit Clock (SCK) |
| WS     | GPIO 27   | Word Select (WS) |
| SD     | GPIO 28   | Serial Data (SD) |
| MUTE   | GPIO 22   | Mute control (active low) |

## Audio Sample Files

The following WAV files must be placed on the SD card:

| Filename | Description | Usage |
|----------|-------------|-------|
| `hdd_spinup.wav` | HDD spinup sound | Played once when system starts |
| `hdd_idle.wav` | HDD idle sound | Looped continuously when no HDD activity |
| `hdd_access.wav` | HDD access sound | Played during HDD read/write operations |

**Audio Format Requirements:**
- **Sample Rate**: 16 kHz
- **Bit Depth**: 16-bit
- **Channels**: Stereo (2 channels)
- **Format**: WAV (PCM)

## Installation & Setup

### 1. Firmware
- Install MicroPython firmware on your Raspberry Pi Pico
- Download from: https://micropython.org/download/rp2-pico/

### 2. Dependencies
- Copy `sdcard.py` to your Pico's `lib/` directory
- Download from: https://github.com/micropython/micropython/tree/master/drivers/sdcard

### 3. Audio Files
- Format an SD card as FAT32
- Copy the required WAV files to the root directory
- Insert the SD card into the SD card module

### 4. Hardware Assembly
- Connect the Pico to the ISA prototyping board according to the pin mapping above
- Connect the Pico Audio Pack to the Pico
- Connect the SD card module to the Pico
- Mount the ISA board in your PC's ISA slot

### 5. Software
- Copy `main.py` and `config.py` to your Pico
- The system will auto-execute `main.py` on boot

## Configuration

Edit `config.py` to customize:
- Pin assignments for different hardware setups
- Audio settings (sample rate, bit depth, channels)
- HDD activity detection parameters
- Audio file names

## Usage

1. **Power On**: The system will automatically start monitoring the ISA bus
2. **Spinup**: HDD spinup sound plays once during initialization
3. **Idle**: HDD idle sound loops continuously when no activity is detected
4. **Access**: HDD access sound plays during read/write operations
5. **Real-time Response**: Audio changes immediately based on detected HDD activity

## How It Works

### ISA Bus Monitoring
The system uses PIO (Programmable I/O) state machines to monitor the ISA bus at high speed:
- **State Machine 0**: Monitors IOR (I/O Read) signals
- **State Machine 1**: Monitors IOW (I/O Write) signals
- **Address Capture**: Captures A0-A9 address lines when control signals are active
- **HDD Detection**: Identifies HDD activity by monitoring ports 0x1F0 (data) and 0x1F7 (status)

### Audio Management
- **Spinup**: Played once at startup to simulate HDD initialization
- **Idle**: Looped continuously when no HDD activity is detected
- **Access**: Interrupts idle sound and plays during HDD operations
- **Seamless Transitions**: Audio switches instantly between states

### SD Card Integration
- **File Loading**: Audio files loaded directly from SD card
- **Real-time Playback**: No buffering delays for immediate response
- **Easy Customization**: Replace WAV files to change sounds

## Media
### Prototype ISA board: August 2025
Initial prototype of an ISA board that can be mounted within the PC to draw power from the ISA +5v rail

![Prototype ISA board](images/ISAPrototype1.jpg)

### Prototype board: August 2025
Using detection of the PC HDD controller activity LED voltage to detect activity and drive the HDD Synth

[![Proof of concept video](https://img.youtube.com/vi/yZhKAbbrKRM/0.jpg)](https://youtu.be/yZhKAbbrKRM)

### Proof of concept: July 2022
Not connected to a PC, but purely to validate if the Pi Pico could produce a convincing sounding HDD subsitution. I'd say it does!

[![Proof of concept video](https://img.youtube.com/vi/V0S9wBl7J3U/0.jpg)](https://youtu.be/V0S9wBl7J3U)



<!--
## Usage


## License
-->

## Contact
Peter Bridger at [maverickuk@gmail.com](maverickuk@gmail.com)

## Resources
- [ISA System Architecture by Tom Shanley](https://archive.org/details/ISA_System_Architecture)
- [Intel ISA Bus Specification](https://archive.org/details/bitsavers_intelbusSpep89_3342148)
- [ISA bus technical summary](http://wearcam.org/ece385/lecture6/isa.htm)

## Acknowledgments
- Inspired by the [HDD Clicker project](https://www.serdashop.com/HDDClicker)
- A big thanks to [Ian Scott of PicoGUS fame](https://picog.us/) for sharing his resource sources and knowledge of using the Pi Pico with the ISA bus which gave me the confidence to take this project to the next level
- [Marten Electric](https://www.martenelectric.cz/) for the excellent ISA prototyping boards which made it very easy to wire up the Pico to my computer