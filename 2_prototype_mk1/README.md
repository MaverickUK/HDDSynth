## HDD Synth
### Phase 2: PCB based prototypes

Phase 1 has established that this project is possible from both a hardware and software perspective. This phase is to create and iterate using a professionally manufactured PCB ready to enter phase 3, which will produce the released board.

![KiCad PCB 3D render](/images/pcb_prototype_mk1.png)

**12th October 2025**

The MK1 prototype was designed to prove that the individual components would work together on an ISA card and be able to detect HDD activity from the ISA bus.

Whilst possible in theory, attempting to detect HDD activity purely from observing the ISA bus read and write requests through 0x1F0 - Data port (actual data transfers) and 0x1F7 - Status port (command/status polling)). Whilst this does work, I've not yet been able to get the detection to be as precise and reliable as my original method of using the HDD activity LED. 

In order to focus on getting a working MVP I've decided to use my original HDD activity method via the LED. This will allow me to focus on ensuring the rest of the hardware and software designs are solid. The ISA HDD activity detection can be revisited in the future.