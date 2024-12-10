import RPi.GPIO as GPIO  # Library for controlling GPIO pins on Raspberry Pi
import time  # Used for handling time delays and timestamps
import logging  # Used for logging distance data to a file
from flask import Flask, jsonify, render_template  # Flask for web server and API

# Flask App setup
app = Flask(__name__)  # Initialize Flask application

# Logging setup
logging.basicConfig(
    filename="distance_log.csv",  # File to store distance logs
    level=logging.INFO,  # Log level set to INFO
    format="%(asctime)s, %(message)s",  # Log format includes timestamp and message
    datefmt="%Y-%m-%d %H:%M:%S"  # Date and time format for the logs
)

# GPIO setup
GPIO.setmode(GPIO.BCM)  # Set GPIO mode to Broadcom SOC channel numbering

# Define GPIO pins for the ultrasonic sensor and LEDs
TRIG_PIN = 14  # GPIO pin for triggering the ultrasonic sensor
ECHO_PIN = 15  # GPIO pin for receiving the ultrasonic sensor echo
LED_PIN_LOW = 16  # GPIO pin for the low threshold LED
LED_PIN_MEDIUM = 17  # GPIO pin for the medium threshold LED
LED_PIN_HIGH = 18  # GPIO pin for the high threshold LED

# Set up GPIO pins
GPIO.setup(TRIG_PIN, GPIO.OUT)  # Set TRIG_PIN as output
GPIO.setup(ECHO_PIN, GPIO.IN)  # Set ECHO_PIN as input
GPIO.setup(LED_PIN_LOW, GPIO.OUT)  # Set LED_PIN_LOW as output
GPIO.setup(LED_PIN_MEDIUM, GPIO.OUT)  # Set LED_PIN_MEDIUM as output
GPIO.setup(LED_PIN_HIGH, GPIO.OUT)  # Set LED_PIN_HIGH as output

# Distance thresholds in centimeters
LOW_THRESHOLD = 10  # Distance below this will light up the low threshold LED
MEDIUM_THRESHOLD = 30  # Distance between LOW and MEDIUM lights up the medium LED

# Variable to store the current distance
current_distance = 0


def log_distance(distance):
    """Log the measured distance to a CSV file."""
    logging.info(f"{distance:.2f}")  # Log distance with 2 decimal places


def setup_leds():
    """Initialize all LEDs to the OFF state."""
    GPIO.output(LED_PIN_LOW, GPIO.LOW)
    GPIO.output(LED_PIN_MEDIUM, GPIO.LOW)
    GPIO.output(LED_PIN_HIGH, GPIO.LOW)


def control_leds(distance):
    """
    Light up LEDs based on the measured distance.
    - Low LED for distance < LOW_THRESHOLD
    - Medium LED for LOW_THRESHOLD ≤ distance < MEDIUM_THRESHOLD
    - High LED for distance ≥ MEDIUM_THRESHOLD
    """
    if distance < LOW_THRESHOLD:
        GPIO.output(LED_PIN_LOW, GPIO.HIGH)  # Turn on low threshold LED
        GPIO.output(LED_PIN_MEDIUM, GPIO.LOW)
        GPIO.output(LED_PIN_HIGH, GPIO.LOW)
    elif distance < MEDIUM_THRESHOLD:
        GPIO.output(LED_PIN_LOW, GPIO.LOW)
        GPIO.output(LED_PIN_MEDIUM, GPIO.HIGH)  # Turn on medium threshold LED
        GPIO.output(LED_PIN_HIGH, GPIO.LOW)
    else:
        GPIO.output(LED_PIN_LOW, GPIO.LOW)
        GPIO.output(LED_PIN_MEDIUM, GPIO.LOW)
        GPIO.output(LED_PIN_HIGH, GPIO.HIGH)  # Turn on high threshold LED


def get_distance():
    """Measure the distance using the ultrasonic sensor."""
    # Send a trigger signal
    GPIO.output(TRIG_PIN, GPIO.HIGH)
    time.sleep(0.00001)  # Trigger signal duration
    GPIO.output(TRIG_PIN, GPIO.LOW)

    # Wait for the echo response
    pulse_start = time.time()
    while GPIO.input(ECHO_PIN) == GPIO.LOW:  # Wait for echo to start
        pulse_start = time.time()
    pulse_end = time.time()
    while GPIO.input(ECHO_PIN) == GPIO.HIGH:  # Wait for echo to end
        pulse_end = time.time()

    # Calculate distance using the speed of sound
    pulse_duration = pulse_end - pulse_start  # Time taken for the pulse
    speed_of_sound = 34300  # Speed of sound in cm/s
    distance = (pulse_duration * speed_of_sound) / 2  # Calculate one-way distance
    return distance


@app.route("/")
def home():
    """Render the homepage with the current distance."""
    global current_distance
    return render_template("index.html", distance=current_distance)  # Pass distance to HTML


@app.route("/distance")
def distance():
    """API endpoint to return the current distance in JSON format."""
    global current_distance
    return jsonify({"distance": current_distance})


def main():
    """Main program loop for continuous distance measurement and control."""
    global current_distance
    try:
        setup_leds()  # Initialize LEDs
        print("Ultrasonic sensor system is running...")
        while True:
            # Measure distance and update the current distance
            current_distance = get_distance()
            print(f"Distance: {current_distance:.2f} cm")

            # Log the distance and control the LEDs
            log_distance(current_distance)
            control_leds(current_distance)

            # Wait before the next reading
            time.sleep(1)  # 1-second delay between measurements

    except KeyboardInterrupt:
        # Handle program interruption (e.g., CTRL+C)
        print("Exiting program.")
    finally:
        # Clean up GPIO pins on exit
        GPIO.cleanup()
        print("GPIO cleanup complete.")


if __name__ == "__main__":
    from threading import Thread

    # Run the Flask server in a separate thread
    flask_thread = Thread(target=lambda: app.run(host="0.0.0.0", port=5000, debug=False))
    flask_thread.daemon = True  # Allow program to exit even if Flask is running
    flask_thread.start()

    # Run the main program loop
    main()
