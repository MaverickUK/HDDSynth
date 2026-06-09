# HDD Synth: Prototype MKIII
Written in CircuitPython for Pi Pico

## Startup Behavior

The SDCARD_REQUIRED setting (configured in settings.py, default False) controls startup behavior:

- **SDCARD_REQUIRED = True (strict mode):** Device requires SD card to start. If no SD card is detected, it will play a NO_SD_CARD beep and not run.
- **SDCARD_REQUIRED = False (relaxed mode):** Device can start without SD card if a sample pack is already installed internally. If no sample pack is installed, it will play a PACK_NOT_FOUND beep. When running without an SD card, the action button is disabled (sample pack switching and factory reset are unavailable).

## settings.json
If this file exists on the SD card install in the HDD Synth it will be read at startup and will override the default HDD Synth settings.

This can be used to configure the HDD Synth to operate in headless mode without any physical controls.

### Settings
- **SIMULATION_MODE:** Boolean. True will simulate HDD activity for testing without actual HDD, False will use real HDD activity signal. Default False
- **PLAY_SPINUP:** Boolean. True will play spinup sound at power on, False will not. Default True
- **PLAY_SPINDOWN:** Boolean. True will play spindown sound at power off, False will not. Default True
- **PLAY_IDLE:** Boolean. True will play idle sound continously, False will not. Default True
- **ACCESS_HOLD_TIME_MS:** Integer. How long to play the access sound for after detect activity stops in milliseconds. Default 500
- **VOLUME_DEFAULT:** Number between 0 and 1. 0 is silence, 1 is full volume. Default 0.5
- **BALANCE_DEFAULT:** Number between 0 and 1. 0 = idle only, 1 = access only, 0.5 balanced idle and access. Default 0.5
- **SAMPLE_PACK:** Name of the sample pack directory on the SD card to use. E.g. If /samples/ibm is desired, this should be set to ibm

### Example settings.json
```
{
    "SIMULATION_MODE": false,
    "PLAY_SPINUP": false,
    "PLAY_SPINDOWN": true,
    "PLAY_IDLE": true,
    "ACCESS_HOLD_TIME_MS": 150,
    "VOLUME_DEFAULT": 0.7,
    "BALANCE_DEFAULT": 0.5,
    "SAMPLE_PACK": "my_pack_name"
}
```