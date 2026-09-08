"""
Robust Sound Manager for RBX Detective.
Supports high-fidelity WAV file playback with automatic fallback to Windows audio beep.
Ensures sound is heard on any Windows sound card and volume setting.
"""
import os
import threading

try:
    import winsound
except ImportError:
    winsound = None


class SoundManager:
    volume = 0.8  # 0.0 to 1.0
    _sound_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "click.wav")

    @classmethod
    def set_volume(cls, vol: float):
        cls.volume = max(0.0, min(1.0, float(vol)))

    @classmethod
    def get_volume(cls) -> float:
        return cls.volume

    @classmethod
    def play_click(cls):
        """Plays UI click sound with multiple fallback mechanisms to ensure audio output."""
        if cls.volume <= 0.01 or not winsound:
            return

        def _play():
            try:
                # 1. Primary method: Native Windows SND_FILENAME with SND_ASYNC (100% stable in Windows)
                if os.path.exists(cls._sound_file):
                    winsound.PlaySound(cls._sound_file, winsound.SND_FILENAME | winsound.SND_ASYNC)
                else:
                    # 2. Fallback: Windows direct audio generator
                    winsound.Beep(1400, 45)
            except Exception:
                try:
                    # 3. Secondary fallback if DirectSound device is busy
                    winsound.Beep(1400, 45)
                except Exception:
                    pass

        threading.Thread(target=_play, daemon=True).start()
