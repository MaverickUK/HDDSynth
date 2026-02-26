import audiobusio
import audiocore
import audiomixer 


import beep
import settings

audio_out = audiobusio.I2SOut(
    bit_clock=settings.AMP_BCK_PIN,
    word_select=settings.AMP_WS_PIN,
    data=settings.AMP_SD_PIN
)

mixer = audiomixer.Mixer(
    voice_count=settings.MIXER_VOICES
)

audio_out.play(mixer)

print("Play beep")
beep.play_beep(mixer, pitch="high", count=3, length="short", volume=0.15)
print("Beep complete")
                