import os
import sys
import time
import random
import subprocess
from motor_control import ScoutBot
from camera_module import ScoutCamera
from gpiozero import DistanceSensor
from gpiozero.pins.rpigpio import RPiGPIOFactory

# --- Configuration ---
FORWARD_DURATION = 2.0      # seconds to move forward
TURN_DURATION = 1.0         # seconds to turn
MAX_SEARCH_ITERATIONS = 50  # Maximum number of move-capture-turn cycles
MIN_DISTANCE_CM = 20        # Minimum distance in cm to an obstacle

# GPIO Pins
ULTRASONIC_TRIGGER_PIN = 23
ULTRASONIC_ECHO_PIN = 24

# Paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
RECOGNIZER_VENV_PYTHON = os.path.join(SCRIPT_DIR, ".facerec_venv/bin/python")
RECOGNIZER_SCRIPT_PATH = os.path.join(SCRIPT_DIR, "recognize_cli.py")

class SearchBot:
    def __init__(self, pin_factory):
        self.scout_bot = ScoutBot(pin_factory=pin_factory)
        self.scout_camera = ScoutCamera()
        self.distance_sensor = DistanceSensor(
            echo=ULTRASONIC_ECHO_PIN,
            trigger=ULTRASONIC_TRIGGER_PIN,
            pin_factory=pin_factory
        )
        print("SearchBot initialized.")

    def search_for_person(self, target_name, max_iterations=MAX_SEARCH_ITERATIONS):
        print(f"\n--- Starting Autonomous Search for {target_name.upper()} ---")
        iteration = 0

        while iteration < max_iterations:
            iteration += 1
            print(f"\n--- Search Iteration {iteration}/{max_iterations} ---")

            # 1. Check for obstacle
            distance = self.distance_sensor.distance * 100
            print(f"  -> Sensor reading: {distance:.2f} cm")
            if distance < MIN_DISTANCE_CM:
                print("Obstacle detected! Backing up and turning...")
                self.scout_bot.backward(speed=0.6, duration=0.5)
                self.scout_bot.right(speed=0.8, duration=TURN_DURATION)
                continue

            # 2. Move Forward
            print("Moving forward...")
            self.scout_bot.forward(speed=0.7, duration=FORWARD_DURATION)

            # 3. Capture and Recognize
            image_path = self.scout_camera.capture_image()
            if image_path is None:
                print("Skipping recognition due to capture failure.")
                self.scout_bot.left(speed=0.8, duration=TURN_DURATION) # Turn to a new view
                continue

            print("Running recognition...")
            try:
                result = subprocess.run(
                    [RECOGNIZER_VENV_PYTHON, RECOGNIZER_SCRIPT_PATH, image_path],
                    capture_output=True, text=True, check=True, timeout=60
                )
                # Get the last non-empty line of output, which contains the names
                last_line = result.stdout.strip().split('\n')[-1]
                recognized_names = [name.strip() for name in last_line.split(',') if name.strip()]
                print(f"  -> Recognition result: {recognized_names}")

                # Perform a case-insensitive check
                if target_name.lower() in [name.lower() for name in recognized_names]:
                    print(f"SUCCESS: Found {target_name}!")
                    self.scout_bot.stop()
                    return True # Target found
            except subprocess.CalledProcessError as e:
                print(f"ERROR: Recognition script failed with exit code {e.returncode}.", file=sys.stderr)
                print(f"  --> Stderr: {e.stderr.strip()}", file=sys.stderr)
            except Exception as e:
                print(f"ERROR: An unexpected error occurred during recognition: {e}", file=sys.stderr)

            # 4. No target found, turn to a new direction
            print(f"Target '{target_name}' not found. Turning to continue search...")
            self.scout_bot.left(speed=0.8, duration=TURN_DURATION)
        
        print("\n--- Max iterations reached. Target not found. ---")
        return False

    def cleanup(self):
        """Cleans up resources."""
        self.scout_bot.cleanup()
        self.scout_camera.cleanup()
        self.distance_sensor.close()
        print("SearchBot resources cleaned up.")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: sudo python search_cli.py <name_to_find>", file=sys.stderr)
        sys.exit(1)

    target_to_find = sys.argv[1]
    
    search_bot = None
    try:
        # RPiGPIOFactory requires sudo, so we run the whole script that way
        factory = RPiGPIOFactory()
        search_bot = SearchBot(pin_factory=factory)
        search_bot.search_for_person(target_to_find)
    except KeyboardInterrupt:
        print("\nSearch interrupted by user.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}", file=sys.stderr)
    finally:
        if search_bot:
            search_bot.cleanup()


