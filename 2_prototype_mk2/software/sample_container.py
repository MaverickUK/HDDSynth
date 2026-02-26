import gc
import os
import random

import audio
import audiocore

# Container for audio samples
class SampleContainer:
    def __init__(self, sample_file):
        self.sample_file = sample_file
        # Store the file handle so we can close it later
        self.file_handle = open(sample_file, "rb")
        self.sample = audiocore.WaveFile(self.file_handle)
        self.duration = audio.get_duration(sample_file, self.sample)

        # Get the file statistics
        stats = os.stat(sample_file)
        self.file_size = stats[6] # stats[6] is the size of the file in bytes        

    def deinit(self):
        self.sample.deinit()  # Clean up the WaveFile object
        self.file_handle.close() # Close the actual file on the SD/Flash


