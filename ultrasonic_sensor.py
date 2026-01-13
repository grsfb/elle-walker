from gpiozero import DistanceSensor
from gpiozero.pins.lgpio import LGPIOFactory # For Raspberry Pi 5 compatibility
from signal import pause
from time import sleep

# --- Configuration ---
# GPIO Pins connected to the HC-SR04 sensor
ULTRASONIC_TRIGGER_PIN = 23
ULTRASONIC_ECHO_PIN = 24

# --- Sensor Initialization ---
# The DistanceSensor class handles the trigger/echo logic and timing.
# It uses the speed of sound to calculate distance.
sensor = DistanceSensor(
    echo=ULTRASONIC_ECHO_PIN,
    trigger=ULTRASONIC_TRIGGER_PIN,
    max_distance=2,  # Maximum distance to measure in meters (adjust as needed)
    queue_len=3,     # Number of values to store for median calculation
    pin_factory=LGPIOFactory()
)

# --- Main Script ---
if __name__ == '__main__':
    print(f"Initializing ultrasonic sensor on Trigger={ULTRASONIC_TRIGGER_PIN}, Echo={ULTRASONIC_ECHO_PIN}")
    print("Move objects in front of the sensor to see distance readings.")
    print("Press Ctrl+C to exit.")

    try:
        # Loop and print distance
        while True:
            distance_cm = round(sensor.distance * 100, 2) # Convert meters to cm
            print(f"Distance: {distance_cm} cm")
            sleep(0.5) # Read every half second
    except KeyboardInterrupt:
        print("\nExiting sensor test.")
    finally:
        sensor.close() # Clean up GPIO resources
        print("Sensor resources cleaned up.")