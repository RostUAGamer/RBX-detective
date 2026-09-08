"""
Sound Manager for RBX Detective.
Generates and plays smooth, pleasant UI click feedback sounds with adjustable volume.
Properly handles Windows winsound playback without blocking the main UI thread.
"""
import os
import math
import struct
import wave
import io
import threading

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
    def _create_sine_click(cls, volume: float, freq: int = 1200, duration: float = 0.05, sample_rate: int = 44100) -> bytes:
        """Synthesizes a crisp, pleasant UI tap/click wave in memory."""
        num_samples = int(sample_rate * duration)
        buf = io.BytesIO()
        with wave.open(buf, 'wb') as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(sample_rate)
            for i in range(num_samples):
                t = float(i) / sample_rate
                # smooth exponential decay envelope
                env = math.exp(-t * 80.0) * volume
                # subtle pitch descent for modern mechanical/soft feel
                cur_freq = freq * (1.0 - 0.3 * (t / duration))
                sample = math.sin(2.0 * math.pi * cur_freq * t) * env
                val = int(sample * 32767.0)
                val = max(-32768, min(32767, val))
                wav.writeframesraw(struct.pack('<h', val))
        return buf.getvalue()

    @classmethod
    def play_click(cls):
        """
        Plays soft click sound asynchronously in a worker thread.
        Note: winsound.SND_MEMORY does not allow SND_ASYNC in Windows API,
        so running PlaySound(SND_MEMORY) in a daemon background thread is the correct solution.
        """
        if cls.volume <= 0.001 or not winsound:
            return

        def _worker():
            v_key = round(cls.volume, 2)
            with cls._lock:
                if v_key not in cls._sound_cache:
                    cls._sound_cache[v_key] = cls._create_sine_click(v_key)
                sound_bytes = cls._sound_cache[v_key]

            try:
                # Play from memory inside thread (instant, non-blocking)
                winsound.PlaySound(sound_bytes, winsound.SND_MEMORY)
            except Exception:
                pass

        threading.Thread(target=_worker, daemon=True).start()
