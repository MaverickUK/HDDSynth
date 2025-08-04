## HDD Synth
![Logo](images/HDDSynthLogoSmall.png)

Recreate the sound of mechanical spinning HDDs on retro PCs that use a solid state drive.

Inspired by seeing the HDD Clicker project and wanting to more faithfully recreate the sound of old mechanical hard drives spinning up and accessing data. Because the hard drive sounds come from samples, it's possible to replace them with any hard drive recording you'd like or something completely different!

The initial prototypes require a hook up to the PCs HDD LED to detect activity, however after advice from [Ian Scott](https://picog.us/) I'm looking into detecting HDD activity directly from the ISA bus which will make this a plug and play device.

## Media
### Prototype ISA board: August 2025
![Prototype ISA board](images/ISAPrototype1.jpg)

### Prototype board: August 2025
[![Proof of concept video](https://img.youtube.com/vi/yZhKAbbrKRM/0.jpg)](https://youtu.be/yZhKAbbrKRM)

### Proof of concept: July 2022
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
- [Marten Electric](https://www.martenelectric.cz/) for his excellent ISA prototyping boards which made it very easy to wire up the Pico to my computer