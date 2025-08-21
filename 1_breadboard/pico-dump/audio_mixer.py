import ustruct
import uio
import math
import urandom

class Sound:
    """Represents a single sound effect or background track."""
    def __init__(self, data, volume=1.0, loop=False):
        # We store the raw bytearray from the 16-bit WAV file.
        self.data = data
        self.pos = 0  # The current position in the bytearray (in bytes)
        self.volume = volume
        self.loop = loop
        self.active = True

    def next_sample(self):
        """
        Reads and returns the next 16-bit sample from the sound's data.
        Returns 0 if the sound is inactive or has finished playing.
        """
        if not self.active:
            return 0

        # Each sample is 2 bytes long, so we check if the position is past the end
        if self.pos >= len(self.data):
            if self.loop:
                self.pos = 0  # Reset position to loop the sound
            else:
                self.active = False
                return 0

        # Unpack a 16-bit signed integer from the bytearray at the current position.
        # '<h' specifies a little-endian signed short (16-bit).
        sample, = ustruct.unpack_from("<h", self.data, self.pos)

        # Move the position forward by 2 bytes (one 16-bit sample)
        self.pos += 2
        
        # Return the sample adjusted by the volume
        return int(sample * self.volume)

    def stop(self):
        """Stops the sound from playing."""
        self.active = False

class Mixer:
    """Manages and mixes multiple active sounds into a single output sample."""
    def __init__(self):
        self.sounds = []

    def add(self, sound):
        """Adds a sound to be mixed."""
        self.sounds.append(sound)

    def mix(self):
        """
        Mixes all active sounds and returns a single 16-bit signed integer.
        The output is clamped to the valid 16-bit range.
        """
        sample = 0
        
        # Iterate through a copy of the list to allow for sounds to be removed
        # if they finish (e.g., from an HDD access stopping).
        sounds_to_remove = []
        for s in self.sounds:
            sample += s.next_sample()
            if not s.active:
                sounds_to_remove.append(s)

        for s in sounds_to_remove:
            self.sounds.remove(s)

        # Clamp the mixed sample to the 16-bit signed integer range (-32768 to 32767)
        sample = max(-32768, min(32767, sample))
        return sample

    @staticmethod
    def load_wav(filename):
        """
        Loads the raw 16-bit audio data from a WAV file by skipping the 44-byte header.
        """
        with open(filename, "rb") as f:
            f.seek(44)  # Skip the WAV header
            return bytearray(f.read())
