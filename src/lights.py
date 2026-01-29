import os
from settings import LED_PIN_MAP

# Check if running in development/mock mode (for local testing without Pi hardware)
DEV_MODE = os.environ.get("DEV_MODE", "false").lower() == "true"

# Try to import GPIO for Raspberry Pi
GPIO_AVAILABLE = False
if not DEV_MODE:
    try:
        import RPi.GPIO as GPIO

        GPIO_AVAILABLE = True
    except ImportError:
        pass


def setup_gpio():
    """Initialize GPIO pins for LED control"""
    if GPIO_AVAILABLE:
        GPIO.setmode(GPIO.BCM)
        # Set up LED pins as outputs
        for led_id, pin in LED_PIN_MAP.items():
            GPIO.setup(pin, GPIO.OUT)
            GPIO.output(pin, GPIO.LOW)  # Start with LEDs off


def cleanup_gpio():
    """Clean up GPIO resources"""
    if GPIO_AVAILABLE:
        GPIO.cleanup()


def set_led_state(pin, state):
    """Set LED state on a GPIO pin"""
    if GPIO_AVAILABLE:
        GPIO.output(pin, state)
    elif DEV_MODE:
        print(f"DEV_MODE: Would set GPIO pin {pin} to {state}")
