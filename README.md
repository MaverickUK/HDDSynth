# HDD Synth
<div style="background: white; display: inline-block; padding: 8px;">
  <img src="images/HDDSynthLogoSmall.png" alt="Logo">
</div>

### Recreates the sound of mechanical spinning HDDs on retro PCs that use a solid state drive.

Inspired by seeing the HDD Clicker project and wanting to more faithfully recreate the sound of old mechanical hard drives spinning up and accessing data. Because the hard drive sounds come from samples, it's possible to replace them with any hard drive recording you'd like or something completely different!

## Features

- **Plug and Play**: Uses direct ISA bus monitoring to detect HDD activity, so all you have to do it plug it in
- **SD Card Storage**: Audio samples stored on removable SD card for easy customization
- **Configurable**: Future software based enhancement planned

## Progress
### ✅ [Phase 1: Breadboard prototype](1_breadboard/README.md) 
### 🔄 [Phase 2: PCB prototype](2_prototype/README.md) 
### 🌱 Phase 3: PCB final 


## Media
[View gallery](media.md)



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