from motor_control import ScoutBot
import RPi.GPIO as GPIO
from time import sleep, time
import sys

# --- Configuration ---
# GPIO Pins connected to the HC-SR04 sensor (using BCM numbering)
ULTRASONIC_TRIGGER_PIN = 23
ULTRASONIC_ECHO_PIN = 24

# Obstacle avoidance parameters
AVOID_DISTANCE_CM = 10 # Distance in cm to stop and avoid
MOVE_SPEED = 1.0       # Speed to move forward (0.0 to 1.0)
TURN_DURATION = 1.5    # Duration in seconds to turn when avoiding
LOOP_DELAY = 0.1       # Delay between sensor readings and motor updates

def get_distance(trigger_pin, echo_pin):
    """
    Gets distance from an HC-SR04 sensor using RPi.GPIO.
    Returns distance in centimeters.
    """
    # Send a 10us pulse to trigger
    GPIO.output(trigger_pin, True)
    sleep(0.00001)
    GPIO.output(trigger_pin, False)

    start_time = time()
    stop_time = time()

    # Save start time
    while GPIO.input(echo_pin) == 0:
        start_time = time()

    # Save time of arrival
    while GPIO.input(echo_pin) == 1:
        stop_time = time()

    # Time difference between start and arrival
    time_elapsed = stop_time - start_time
    # Multiply with the sonic speed (34300 cm/s)
    # and divide by 2, because there and back
    distance = (time_elapsed * 34300) / 2

    return distance

class ObstacleAvoider:
    def __init__(self):
        print("Initializing ObstacleAvoider...")
        # Initialize robot - this will use RPiGPIOFactory internally
        self.scout_bot = ScoutBot()
        
        # Initialize sensor pins manually using RPi.GPIO
        print("Initializing sensor pins with RPi.GPIO...")
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(ULTRASONIC_TRIGGER_PIN, GPIO.OUT)
        GPIO.setup(ULTRASONIC_ECHO_PIN, GPIO.IN)
        # Ensure trigger is low
        GPIO.output(ULTRASONIC_TRIGGER_PIN, False)
        sleep(1) # Allow sensor to settle

        print("ObstacleAvoider initialized.")

    def move_forward_avoiding_obstacles(self):
        print(f"Starting autonomous travel (avoidance distance: {AVOID_DISTANCE_CM}cm)...")
        print("Robot will move forward, stop and turn right if an obstacle is detected.")
        print("Press Ctrl+C to stop.")

        try:
            while True:
                distance_cm = get_distance(ULTRASONIC_TRIGGER_PIN, ULTRASONIC_ECHO_PIN)
                print(f"  -> Sensor reading: {distance_cm:.2f} cm") # Debugging print
                
                if distance_cm < AVOID_DISTANCE_CM:
                    print(f"Obstacle detected at {distance_cm:.2f} cm! Avoiding...")
                    self.scout_bot.stop()
                    # Back up to create space
                    print("  -> Backing up...")
                    self.scout_bot.backward(speed=0.6, duration=0.5)
                    # Turn right
                    print("  -> Turning right...")
                    self.scout_bot.right(speed=0.8, duration=TURN_DURATION)
                    self.scout_bot.stop() # Stop after turn
                    print("Avoidance maneuver complete. Resuming forward movement.")
                else:
                    self.scout_bot.forward(speed=MOVE_SPEED)
                    sleep(0.01) # Small pause to ensure motor command engages
                
                sleep(LOOP_DELAY) # Small delay to control loop speed

        except KeyboardInterrupt:
            print("\nAutonomous travel stopped by user.")
        except Exception as e:
            print(f"An error occurred during autonomous travel: {e}", file=sys.stderr)
        finally:
            self.scout_bot.stop() # Ensure robot stops
            self.cleanup()

    def cleanup(self):
        print("Cleaning up resources...")
        self.scout_bot.cleanup()
        GPIO.cleanup() # Clean up RPi.GPIO pins
        print("Resources cleaned up.")

# --- Main Script Execution ---
if __name__ == '__main__':
    avoider = None
    try:
        avoider = ObstacleAvoider()
        avoider.move_forward_avoiding_obstacles()
    except Exception as e:
        print(f"Failed to start ObstacleAvoider: {e}", file=sys.stderr)
    finally:
        if avoider:
            # Cleanup is now called inside the class's own finally block
            pass

