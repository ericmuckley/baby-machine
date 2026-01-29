import os
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
        
        try:
            self.audio_stream = self.p.open(
                format=pyaudio.paFloat32,
                channels=1,
                rate=sample_rate,
                output=True
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

def generate_video_frames():
    """Generate video frames from camera"""
    camera = None
    picam2 = None
    
    try:
        if PICAMERA2_AVAILABLE:
            # Use Raspberry Pi Camera Module
            print("Using Raspberry Pi Camera Module")
            picam2 = Picamera2()
            config = picam2.create_preview_configuration(main={"size": (640, 480)})
            picam2.configure(config)
            picam2.start()
            
            while True:
                frame = picam2.capture_array()
                
                # Convert RGB to BGR for JPEG encoding
                frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                
                # Encode frame as JPEG
                ret, buffer = cv2.imencode('.jpg', frame)
                frame = buffer.tobytes()
                
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        else:
            # Use OpenCV for PC/USB camera
            camera = cv2.VideoCapture(0)
            
            while True:
                success, frame = camera.read()
                if not success:
                    # If no camera, generate a placeholder
                    frame = np.zeros((480, 640, 3), dtype=np.uint8)
                    cv2.putText(frame, 'No Camera Detected', (150, 240), 
                               cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                
                # Encode frame as JPEG
                ret, buffer = cv2.imencode('.jpg', frame)
                frame = buffer.tobytes()
                
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
    except Exception as e:
        print(f"Video error: {e}")
    finally:
        if camera:
            camera.release()
        if picam2:
            picam2.stop()

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
