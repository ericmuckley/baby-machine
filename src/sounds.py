import os
import sys

# Suppress ALSA/JACK warnings on Raspberry Pi BEFORE importing audio libraries
# These warnings are harmless but noisy
if sys.platform == "linux":
    os.environ["JACK_NO_START_SERVER"] = "1"
    # Suppress ALSA error messages
    try:
        from ctypes import CDLL, c_char_p, c_int, CFUNCTYPE

        ERROR_HANDLER_FUNC = CFUNCTYPE(None, c_char_p, c_int, c_char_p, c_int, c_char_p)

        def py_error_handler(filename, line, function, err, fmt):
            pass  # Silently ignore ALSA errors

        c_error_handler = ERROR_HANDLER_FUNC(py_error_handler)
        asound = CDLL("libasound.so.2")
        asound.snd_lib_error_set_handler(c_error_handler)
    except Exception:
        pass

import numpy as np
import pyaudio
import time


class WhiteNoiseGenerator:
    """Encapsulates white noise generation state and functionality"""

    def __init__(self):
        self.playing = False
        self.audio_stream = None
        self.p = None
        self.volume = 0.5

    def generate(self, volume):
        """Generate white noise audio stream"""
        self.volume = volume

        if self.p is None:
            self.p = pyaudio.PyAudio()

        sample_rate = 44100

        # Find the default output device
        device_index = None
        try:
            # Try to find a working output device
            default_info = self.p.get_default_output_device_info()
            device_index = default_info.get("index")
        except Exception:
            # Fall back to searching for any output device
            for i in range(self.p.get_device_count()):
                try:
                    info = self.p.get_device_info_by_index(i)
                    if info.get("maxOutputChannels", 0) > 0:
                        device_index = i
                        break
                except Exception:
                    continue

        try:
            self.audio_stream = self.p.open(
                format=pyaudio.paFloat32,
                channels=1,
                rate=sample_rate,
                output=True,
                output_device_index=device_index,
            )

            while self.playing:
                # Generate white noise
                noise = np.random.uniform(-1, 1, sample_rate // 10)
                noise = (noise * self.volume).astype(np.float32)
                self.audio_stream.write(noise.tobytes())
        except Exception as e:
            print(f"Audio error: {e}")
        finally:
            if self.audio_stream:
                self.audio_stream.stop_stream()
                self.audio_stream.close()
                self.audio_stream = None

    def start(self, volume=0.5):
        """Start playing white noise"""
        self.volume = volume
        self.playing = True

    def stop(self):
        """Stop playing white noise"""
        self.playing = False

    def set_volume(self, volume):
        """Update volume"""
        self.volume = max(0.0, min(1.0, float(volume)))


# Create a singleton instance for the app to use
white_noise_generator = WhiteNoiseGenerator()


def generate_audio_stream():
    """Generate audio stream from microphone"""
    p = pyaudio.PyAudio()
    stream = None

    try:
        stream = p.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=44100,
            input=True,
            frames_per_buffer=1024,
        )

        while True:
            data = stream.read(1024)
            yield data
    except Exception as e:
        print(f"Microphone error: {e}")
        # Generate silence if no microphone with rate limiting
        while True:
            yield b"\x00" * 2048
            time.sleep(1024 / 44100)  # Match audio sampling rate
    finally:
        if stream:
            stream.stop_stream()
            stream.close()
        p.terminate()
