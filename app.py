import os
import threading
from flask import Flask, render_template, Response, jsonify, request
from src.sounds import white_noise_generator, generate_audio_stream
from src.video import generate_video_frames
from src.lights import setup_gpio, set_led_state
from settings import APP_PORT, white_noise_volume, LED_PIN_MAP

app = Flask(__name__)

# LED state tracking
led_states = {
    "led1": False,
    "led2": False,
}


@app.route("/")
def index():
    """Serve the main HTML page"""
    return render_template("index.html")


@app.route("/toggle_led/<led_id>", methods=["POST"])
def toggle_led(led_id):
    """Toggle LED state"""
    if led_id in led_states:
        led_states[led_id] = not led_states[led_id]

        # Control the GPIO pin for this LED
        if led_id in LED_PIN_MAP:
            set_led_state(LED_PIN_MAP[led_id], led_states[led_id])

        return jsonify({"success": True, "led": led_id, "state": led_states[led_id]})

    return jsonify({"success": False, "error": "Invalid LED ID"}), 400


@app.route("/led_status")
def led_status():
    """Get current LED states"""
    return jsonify(led_states)


@app.route("/video_feed")
def video_feed():
    """Video streaming route"""
    return Response(
        generate_video_frames(), mimetype="multipart/x-mixed-replace; boundary=frame"
    )


@app.route("/audio_feed")
def audio_feed():
    """Audio streaming route"""
    return Response(generate_audio_stream(), mimetype="audio/x-raw")


@app.route("/white_noise/start", methods=["POST"])
def start_white_noise():
    """Start white noise generation"""
    global white_noise_volume

    data = request.json or {}
    volume = data.get("volume", 0.5)
    white_noise_volume = max(0.0, min(1.0, float(volume)))

    if not white_noise_generator.playing:
        white_noise_generator.start(white_noise_volume)
        thread = threading.Thread(
            target=white_noise_generator.generate, args=(white_noise_volume,)
        )
        thread.daemon = True
        thread.start()

    return jsonify({"success": True, "volume": white_noise_volume})


@app.route("/white_noise/stop", methods=["POST"])
def stop_white_noise():
    """Stop white noise generation"""
    white_noise_generator.stop()

    return jsonify({"success": True})


@app.route("/white_noise/volume", methods=["POST"])
def set_white_noise_volume():
    """Set white noise volume"""
    global white_noise_volume

    data = request.json or {}
    volume = data.get("volume", 0.5)
    white_noise_volume = max(0.0, min(1.0, float(volume)))
    white_noise_generator.set_volume(volume)

    return jsonify({"success": True, "volume": white_noise_volume})


if __name__ == "__main__":
    # Initialize GPIO for LED control
    setup_gpio()

    # Use debug mode only in development, set via environment variable
    debug_mode = os.environ.get("FLASK_DEBUG", "False").lower() == "true"
    app.run(host="0.0.0.0", port=APP_PORT, debug=debug_mode, threaded=True)
