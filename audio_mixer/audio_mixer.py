import ustruct
import uio
import math
import urandom

class Sound:
    def __init__(self, data, volume=1.0, loop=False):
        self.data = data
        self.pos = 0
        self.volume = volume
        self.loop = loop
        self.active = True

    def next_sample(self):
        if not self.active:
            return 0
        if self.pos >= len(self.data):
            if self.loop:
                self.pos = 0
            else:
                self.active = False
                return 0
        sample = self.data[self.pos]
        self.pos += 1
        return int(sample * self.volume)

class Mixer:
    def __init__(self):
        self.sounds = []

    def add(self, sound):
        self.sounds.append(sound)

    def mix(self):
        sample = 0
        for s in self.sounds:
            sample += s.next_sample()
        sample = max(0, min(255, sample))  # Clamp
        return sample

    @staticmethod
    def load_wav(filename):
        with open(filename, "rb") as f:
            f.seek(44)  # Skip WAV header
            return bytearray(f.read())
