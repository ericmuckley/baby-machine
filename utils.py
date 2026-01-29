import os
import sys

# Suppress ALSA/JACK warnings on Raspberry Pi BEFORE importing audio libraries
# These warnings are harmless but noisy
if sys.platform == 'linux':
    os.environ['JACK_NO_START_SERVER'] = '1'
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

import cv2
import numpy as np
import pyaudio
import time

# Check if running in development/mock mode (for local testing without Pi hardware)
DEV_MODE = os.environ.get('DEV_MODE', 'false').lower() == 'true'

# Try to import picamera2 for Raspberry Pi
PICAMERA2_AVAILABLE = False
if not DEV_MODE:
    try:
        from picamera2 import Picamera2
        PICAMERA2_AVAILABLE = True
    except ImportError:
        pass

if DEV_MODE:
    print("Running in DEV_MODE - using laptop camera/mic instead of Pi hardware")

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
            device_index = default_info.get('index')
        except Exception:
            # Fall back to searching for any output device
            for i in range(self.p.get_device_count()):
                try:
                    info = self.p.get_device_info_by_index(i)
                    if info.get('maxOutputChannels', 0) > 0:
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
                output_device_index=device_index
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


class CameraManager:
    """Singleton camera manager to handle camera lifecycle properly"""
    
    def __init__(self):
        self.picam2 = None
        self.cv_camera = None
        self.lock = threading.Lock()
        self.started = False
    
    def _init_picamera(self):
        """Initialize Raspberry Pi camera"""
        if self.picam2 is None:
            self.picam2 = Picamera2()
            config = self.picam2.create_preview_configuration(main={"size": (640, 480)})
            self.picam2.configure(config)
        
        if not self.started:
            self.picam2.start()
            self.started = True
    
    def _init_cv_camera(self):
        """Initialize OpenCV camera"""
        if self.cv_camera is None or not self.cv_camera.isOpened():
            self.cv_camera = cv2.VideoCapture(0)
    
    def get_frame(self):
        """Get a single frame from the camera"""
        with self.lock:
            if PICAMERA2_AVAILABLE:
                self._init_picamera()
                frame = self.picam2.capture_array()
                # Convert RGB to BGR for JPEG encoding
                frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            else:
                self._init_cv_camera()
                success, frame = self.cv_camera.read()
                if not success:
                    # If no camera, generate a placeholder
                    frame = np.zeros((480, 640, 3), dtype=np.uint8)
                    cv2.putText(frame, 'No Camera Detected', (150, 240), 
                               cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            
            return frame
    
    def release(self):
        """Release camera resources"""
        with self.lock:
            if self.cv_camera:
                self.cv_camera.release()
                self.cv_camera = None
            if self.picam2 and self.started:
                self.picam2.stop()
                self.started = False
                self.picam2.close()
                self.picam2 = None


# Need threading for the lock
import threading

# Create singleton camera manager
camera_manager = CameraManager()


def generate_video_frames():
    """Generate video frames from camera"""
    try:
        while True:
            frame = camera_manager.get_frame()
            
            # Encode frame as JPEG
            ret, buffer = cv2.imencode('.jpg', frame)
            frame_bytes = buffer.tobytes()
            
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
    except GeneratorExit:
        # Client disconnected, this is normal on page refresh
        pass
    except Exception as e:
        print(f"Video error: {e}")

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
            frames_per_buffer=1024
        )
        
        while True:
            data = stream.read(1024)
            yield data
    except Exception as e:
        print(f"Microphone error: {e}")
        # Generate silence if no microphone with rate limiting
        while True:
            yield b'\x00' * 2048
            time.sleep(1024 / 44100)  # Match audio sampling rate
    finally:
        if stream:
            stream.stop_stream()
            stream.close()
        p.terminate()
