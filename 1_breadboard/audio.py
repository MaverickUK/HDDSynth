"""
Audio Management Module for HDDSynth
Handles audio playback through the Pico Audio Pack.
"""

import board
import audiobusio
import audiocore
import digitalio
import time

class AudioManager:
    """Manages audio playback for HDDSynth."""
    
    def __init__(self, config):
        """Initialize audio manager with configuration."""
        self.config = config
        self.audio_out = None
        self.mute_pin = None
        self.current_audio = None
        self.audio_state = 'stopped'  # 'stopped', 'playing', 'paused'
        
        # Initialize audio system
        self._init_audio_system()
    
    def _init_audio_system(self):
        """Initialize I2S audio output and mute pin."""
        try:
            # Initialize I2S audio output
            self.audio_out = audiobusio.I2SOut(
                bit_clock=getattr(board, f"GP{self.config.BCK_PIN}"),
                word_select=getattr(board, f"GP{self.config.WS_PIN}"),
                data=getattr(board, f"GP{self.config.SD_PIN}")
            )
            print("✅ I2S audio system initialized")
            
            # Initialize mute pin (active low)
            self.mute_pin = digitalio.DigitalInOut(getattr(board, f"GP{self.config.MUTE_PIN}"))
            self.mute_pin.direction = digitalio.Direction.OUTPUT
            self.mute_pin.value = True  # Start muted
            print("✅ Mute pin initialized (started muted)")
            
        except Exception as e:
            print(f"❌ Audio system initialization failed: {e}")
            self.audio_out = None
            self.mute_pin = None
    
    def unmute(self):
        """Unmute the audio amplifier."""
        if self.mute_pin:
            self.mute_pin.value = False
            print("🔊 Audio unmuted")
    
    def mute(self):
        """Mute the audio amplifier."""
        if self.mute_pin:
            self.mute_pin.value = True
            print("🔇 Audio muted")
    
    def play_audio_file(self, file_obj, loop=False):
        """Play an audio file with optional looping."""
        if not self.audio_out or not file_obj:
            print("❌ Cannot play audio: audio system not initialized or file not available")
            return False
        
        try:
            # Create WaveFile object from file
            wave_file = audiocore.WaveFile(file_obj)
            
            # Unmute before playing
            self.unmute()
            
            # Play the audio
            if loop:
                self.audio_out.play(wave_file, loop=True)
                print("🔄 Playing audio file with loop")
            else:
                self.audio_out.play(wave_file)
                print("▶️  Playing audio file")
            
            self.current_audio = wave_file
            self.audio_state = 'playing'
            return True
            
        except Exception as e:
            print(f"❌ Error playing audio: {e}")
            return False
    
    def play_spinup_sound(self, file_obj):
        """Play the HDD spinup sound and wait for completion."""
        if not self.play_audio_file(file_obj, loop=False):
            return False
        
        print("🔄 Playing spinup sound...")
        
        # Wait for spinup sound to complete
        while self.audio_out.playing:
            time.sleep(0.1)
        
        print("✅ Spinup sound completed")
        self.audio_state = 'stopped'
        return True
    
    def play_idle_sound(self, file_obj):
        """Start playing the idle sound in a loop."""
        return self.play_audio_file(file_obj, loop=True)
    
    def play_access_sound(self, file_obj):
        """Play the HDD access sound (interrupts idle loop)."""
        if not self.audio_out or not file_obj:
            return False
        
        try:
            # Stop current audio
            self.audio_out.stop()
            
            # Create and play access sound
            wave_file = audiocore.WaveFile(file_obj)
            self.audio_out.play(wave_file)
            
            self.current_audio = wave_file
            self.audio_state = 'playing'
            print("💾 Playing HDD access sound")
            return True
            
        except Exception as e:
            print(f"❌ Error playing access sound: {e}")
            return False
    
    def resume_idle_sound(self, file_obj):
        """Resume playing the idle sound after access sound completes."""
        if not self.audio_out or not file_obj:
            return False
        
        try:
            # Stop current audio
            self.audio_out.stop()
            
            # Resume idle sound
            wave_file = audiocore.WaveFile(file_obj)
            self.audio_out.play(wave_file, loop=True)
            
            self.current_audio = wave_file
            self.audio_state = 'playing'
            print("🔄 Resumed idle sound loop")
            return True
            
        except Exception as e:
            print(f"❌ Error resuming idle sound: {e}")
            return False
    
    def stop_audio(self):
        """Stop all audio playback."""
        if self.audio_out:
            self.audio_out.stop()
            self.audio_state = 'stopped'
            print("⏹️  Audio stopped")
    
    def is_playing(self):
        """Check if audio is currently playing."""
        return self.audio_out and self.audio_out.playing
    
    def get_audio_state(self):
        """Get current audio state."""
        return self.audio_state
    
    def cleanup(self):
        """Clean up audio resources."""
        try:
            if self.audio_out:
                self.audio_out.stop()
                print("✅ Audio stopped")
            
            if self.mute_pin:
                self.mute_pin.value = True  # Mute before cleanup
                self.mute_pin.deinit()
                print("✅ Mute pin cleaned up")
                
        except Exception as e:
            print(f"⚠️  Error during audio cleanup: {e}")
