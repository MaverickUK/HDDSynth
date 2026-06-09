# HDD Synth: Prototype MKIII
Written in CircuitPython for Pi Pico

## settings.json
If this file exists on the SD card install in the HDD Synth it will be read at startup and will override the default HDD Synth settings.

This can be used to configure the HDD Synth to operate in headless mode without any physical controls.

### Settings
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
    "PLAY_SPINUP": false,
    "PLAY_SPINDOWN": true,
    "PLAY_IDLE": true,
    "ACCESS_HOLD_TIME_MS": 150,
    "VOLUME_DEFAULT": 0.7,
    "BALANCE_DEFAULT": 0.5,
    "SAMPLE_PACK": "my_pack_name"
}
```