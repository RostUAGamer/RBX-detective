"""
Sound Manager for RBX Detective.
Generates and plays smooth, pleasant UI click feedback sounds with adjustable volume.
"""
import os
import math
import struct
import wave
import io
import threading

# Windows native audio playback
try:
    import winsound
except ImportError:
    winsound = None


class SoundManager:
    volume = 0.7  # 0.0 to 1.0
    _sound_cache = {}
    _lock = threading.Lock()

    @classmethod
    def set_volume(cls, vol: float):
        cls.volume = max(0.0, min(1.0, float(vol)))

    @classmethod
    def get_volume(cls) -> float:
        return cls.volume

    @classmethod
    def _create_sine_click(cls, volume: float, freq: int = 1100, duration: float = 0.04, sample_rate: int = 44100) -> bytes:
        """Synthesizes a soft, clean UI tap/click wave in memory."""
        num_samples = int(sample_rate * duration)
        buf = io.BytesIO()
        with wave.open(buf, 'wb') as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(sample_rate)
            for i in range(num_samples):
                t = float(i) / sample_rate
                # smooth exponential decay
                env = math.exp(-t * 90.0) * volume
                # subtle pitch descent
                cur_freq = freq * (1.0 - 0.25 * (t / duration))
                sample = math.sin(2.0 * math.pi * cur_freq * t) * env
                val = int(sample * 32767.0)
                val = max(-32768, min(32767, val))
                wav.writeframesraw(struct.pack('<h', val))
        return buf.getvalue()

    @classmethod
    def play_click(cls):
        """Plays soft click sound asynchronously if volume > 0."""
        if cls.volume <= 0.001 or not winsound:
            return

        def _worker():
            with cls._lock:
                # Quantize volume to 0.05 step to keep cache small
                v_key = round(cls.volume, 2)
                if v_key not in cls._sound_cache:
                    cls._sound_cache[v_key] = cls._create_sine_click(v_key)
                sound_bytes = cls._sound_cache[v_key]
                try:
                    winsound.PlaySound(sound_bytes, winsound.SND_MEMORY | winsound.SND_ASYNC)
                except Exception:
                    pass

        threading.Thread(target=_worker, daemon=True).start()
