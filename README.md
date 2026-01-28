# Baby machine

Multi-purpose sound and light machine designed to run on raspberry pi.

## Features

### Frontend (Single HTML Page)
- **Alpine.js** for reactive interactivity
- **TailwindCSS** for modern, responsive styling
- **Three LED Control Buttons** to toggle LEDs on/off
- **Video Feed** displaying live camera stream
- **Audio Feed** for monitoring microphone input
- **White Noise Generator** with volume slider control

### Backend (Flask Application)
- LED control endpoints for toggling three LEDs
- Video streaming from camera
- Audio streaming from microphone
- White noise generation with adjustable volume


## Stack

- Flask web server
- Alpine JS + Tailwind single page app


## Setup


1. SSH into the raspberry pi (`ssh pi@pi_ip_address`) or open a termial in the raspberry pi.

1. Clone the repository:
    ```bash
    git clone https://github.com/ericmuckley/baby-machine.git
    cd baby-machine
    ```

1. Install Python dependencies:
    ```bash
    python3 -m venv venv
    . venv/bin/activate
    pip install -U pip
    pip install flask numpy opencv-python pyaudio picamera2
    ```

    If you encounter issues installing PyAudio, you may need to install PortAudio first:

    ```bash
    sudo apt install python3-pyaudio
    ```

    For OpenCV on Raspberry Pi:
    ```bash
    sudo apt-get install python3-opencv
    ```

1. Start the Flask application:
    ```bash
    . venv/bin/activate
    python app.py
    ```

1. Open a web browser and navigate to:
    ```
    http://localhost:5000
    ```

    Or from another device on the same network:
    ```
    http://<pi_ip_address>:3000
    ```

3. Use the web interface to:
   - Toggle LEDs on/off
   - View the video feed from the camera
   - Listen to the audio feed from the microphone
   - Control white noise generation and volume

## Raspberry Pi GPIO Setup

For LED control on Raspberry Pi, you'll need to:

1. Connect LEDs to GPIO pins (with appropriate resistors)
2. Modify `app.py` to include GPIO control code:

```python
import RPi.GPIO as GPIO

# Setup GPIO pins
LED_PINS = {
    'led1': 17,  # GPIO pin for LED 1
    'led2': 27,  # GPIO pin for LED 2
    'led3': 22   # GPIO pin for LED 3
}

GPIO.setmode(GPIO.BCM)
for pin in LED_PINS.values():
    GPIO.setup(pin, GPIO.OUT)
    GPIO.output(pin, GPIO.LOW)

# In the toggle_led function:
GPIO.output(LED_PINS[led_id], GPIO.HIGH if led_states[led_id] else GPIO.LOW)
```

## License

MIT License
