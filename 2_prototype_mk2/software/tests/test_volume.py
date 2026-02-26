import time
import board
import array
import math
import audiobusio
import audiocore
import audiomixer  # 1. Import the mixer
import analogio

# Audio pin configuration
BCK_PIN = 16 
WS_PIN = 17
SD_PIN = 18

# Initialize the potentiometer on GP27 (ADC1)
pot = analogio.AnalogIn(board.GP27)

def main():
    try:
        # 2. Initialize I2S Hardware
        audio_out = audiobusio.I2SOut(board.GP16, board.GP17, board.GP18)

        # 3. Initialize the Mixer
        # sample_rate should match your audio data
        mixer = audiomixer.Mixer(voice_count=1, sample_rate=22050, channel_count=1,
                                 bits_per_sample=16, samples_signed=False)
        
        # 4. Point the I2S output to the Mixer instead of the raw sample
        audio_out.play(mixer)

        # Generate the tone
        sample_rate = 22050
        frequency = 440
        samples_per_cycle = int(sample_rate / frequency)
        sine_wave = array.array("H", [0] * samples_per_cycle)
        for i in range(samples_per_cycle):
            value = int(32767 * math.sin(2 * math.pi * i / samples_per_cycle))
            sine_wave[i] = value + 32768 
        
        tone_sample = audiocore.RawSample(sine_wave, sample_rate=sample_rate)

        # 6. Play the sample ONCE before the loop starts
        print("Playing tone through mixer...")
        mixer.voice[0].play(tone_sample, loop=True)
        
        last_level = -1 # Track the last level to reduce print spam

        while True:
            # 1. Read the pot
            raw_value = pot.value
            
            # 2. Calculate level (0.0 to 1.0)
            current_level = raw_value / 65535
            
            # 3. Only update if the value has changed significantly (noise filter)
            if abs(current_level - last_level) > 0.05:
                mixer.voice[0].level = current_level
                print(f"Volume: {current_level * 100:.1f}%")
                last_level = current_level
            
            # Small sleep to keep the CPU from maxing out, 
            time.sleep(0.01)

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()