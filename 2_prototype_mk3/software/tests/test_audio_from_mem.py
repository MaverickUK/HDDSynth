import os, board, audiobusio, array, struct, audiomixer, gc
from audiocore import RawSample

import sdcard
import settings

# Initilise the SD card for samples storage
sdcard.initilise()


# Read mono 16-bit PCM WAV and convert with streaming chunked I/O
def convert_pcm16_signed_to_unsigned_streaming(path):
    """Load WAV and convert to RawSample without holding entire PCM payload in RAM.
    
    Reads and converts the WAV in 4KB chunks to minimize peak memory usage.
    """
    print(f"Loading WAV from {path}...")
    
    with open(path, "rb") as f:
        # Parse RIFF/WAVE header
        hdr = f.read(12)
        if len(hdr) < 12 or hdr[0:4] != b'RIFF' or hdr[8:12] != b'WAVE':
            raise ValueError("Not a valid WAV file (missing RIFF/WAVE)")
        
        sr = None
        ch = None
        bits = None
        data_pos = None
        data_len = None
        
        # Find fmt and data chunks
        while True:
            h = f.read(8)
            if len(h) < 8:
                break
            ck = h[0:4]
            sz = int.from_bytes(h[4:8], "little")
            
            if ck == b'fmt ':
                fmt = f.read(sz)
                if len(fmt) < 16:
                    raise ValueError("Invalid fmt chunk")
                ch = int.from_bytes(fmt[2:4], "little")
                sr = int.from_bytes(fmt[4:8], "little")
                bits = int.from_bytes(fmt[14:16], "little")
            elif ck == b'data':
                data_pos = f.tell()
                data_len = sz
                break
            else:
                f.seek(sz + (sz & 1), 1)
            
            # skip pad byte if chunk size is odd
            if sz & 1:
                f.seek(1, 1)
        
        if not (sr and ch == 1 and bits == 16 and data_pos and data_len):
            raise ValueError(f"Unsupported WAV: channels={ch} bits={bits} sr={sr}")
        
        print(f"Data chunk: {data_len} bytes, sample rate {sr} Hz")
        
        # Read and convert in 4KB chunks to avoid large allocations
        f.seek(data_pos)
        pcm_unsigned = array.array('H')
        chunk_size = 4096  # 4KB chunks
        total_read = 0
        
        try:
            while total_read < data_len:
                to_read = min(chunk_size, data_len - total_read)
                chunk = f.read(to_read)
                if not chunk:
                    break
                
                # Convert this chunk: signed 16-bit bytes -> unsigned 16-bit
                for i in range(0, len(chunk), 2):
                    if i + 1 < len(chunk):
                        low = chunk[i]
                        high = chunk[i + 1]
                        val = (high << 8) | low
                        if val & 0x8000:
                            val -= 0x10000
                        val = (val + 0x8000) & 0xFFFF
                        pcm_unsigned.append(val)
                
                total_read += len(chunk)
                if total_read % 65536 == 0:  # Progress every ~64KB
                    print(f"  Loaded {total_read}/{data_len} bytes...")
        except MemoryError:
            print(f"MemoryError after loading {total_read}/{data_len} bytes")
            raise
        
        print(f"Creating RawSample ({len(pcm_unsigned)} samples)...")
        sample = RawSample(pcm_unsigned, sample_rate=sr)
        gc.collect()
        
        return sample, sr


# Load both samples using streaming chunked conversion
sample, sr = convert_pcm16_signed_to_unsigned_streaming("sd/idle.wav")
sample2, sr = convert_pcm16_signed_to_unsigned_streaming("sd/access.wav") 


# pcm, sample_rate, bits_per_sample = load_wav_from_sd("sd/idle.wav")
# sample = RawSample(pcm, sample_rate=sample_rate)

mixer = audiomixer.Mixer(voice_count=1, sample_rate=sr, channel_count=1, bits_per_sample=16, samples_signed=False) 

print("Sample rate: ", sr) 
# print("Bits per sample: ", bits_per_sample)

i2s = audiobusio.I2SOut(bit_clock=settings.AMP_BCK_PIN, word_select=settings.AMP_WS_PIN, data=settings.AMP_SD_PIN)

#i2s.play(sample) 
#
#while i2s.playing:
#    pass

i2s.play(mixer)
voice = mixer.voice[0]
voice.level = 0.05

repeat = 10000

# Play the sample X times in a loop
for loop_num in range(repeat):
    print(f"Playing sample {loop_num + 1}/{repeat}")
    voice.play(sample)
    while voice.playing:
        pass

    voice.play(sample2)
    while voice.playing:
        pass
    print(f"Finished playback {loop_num + 1}/{repeat}")

print('Done')