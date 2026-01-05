import subprocess
import os
import sys
import time
import random

# Import robot control classes
from motor_control import ScoutBot
from camera_module import ScoutCamera

# --- Configuration ---
FORWARD_DURATION = 1.5  # seconds to move forward
TURN_DURATION = 0.5     # seconds to turn (will be randomized)
MAX_SEARCH_ITERATIONS = 20 # Maximum number of move-capture-turn cycles

# Paths to the recognition script and its virtual environment
RECOGNIZER_VENV_PYTHON = os.path.expanduser("~/elle-walker/.facerec_venv/bin/python")
RECOGNIZER_SCRIPT_PATH = os.path.expanduser("~/elle-walker/recognize_cli.py")

class SearchBot:
    def __init__(self):
        self.scout_bot = ScoutBot()
        self.scout_camera = ScoutCamera()
        print("SearchBot initialized.")

    def search_for_person(self, max_iterations=MAX_SEARCH_ITERATIONS):
        """
        Implements a basic roaming search for a person.
        """
        person_found = False
        iteration = 0
        print("\n--- Starting Autonomous Search for Person ---")

        while not person_found and iteration < max_iterations:
            iteration += 1
            print(f"\n--- Search Iteration {iteration}/{max_iterations} ---")

            # 1. Move Forward
            print("Moving forward...")
            self.scout_bot.forward(duration=FORWARD_DURATION)
            self.scout_bot.stop() # Ensure stop after duration

            # 2. Capture Image
            print("Capturing image...")
            try:
                image_path = self.scout_camera.capture_image()
            except Exception as e:
                print(f"ERROR: Failed to capture image: {e}", file=sys.stderr)
                continue # Skip to next iteration if camera fails

            # 3. Run Recognition
            print("Running recognition...")
            recognized_names = []
            try:
                recognition_result = subprocess.run(
                    [RECOGNIZER_VENV_PYTHON, RECOGNIZER_SCRIPT_PATH, image_path],
                    capture_output=True, text=True, check=True, timeout=60 # Timeout recognition
                )
                recognized_names_str = recognition_result.stdout.strip()
                # Split by comma and filter out empty strings if any
                recognized_names = [name.strip() for name in recognized_names_str.split(',') if name.strip()]

                print(f"Recognition Output: {recognized_names}")

                # Check if any person was detected (known or unknown)
                # "No persons detected." is also a possible output from recognize_cli.py
                if recognized_names and "No persons detected." not in recognized_names:
                    person_found = True
                    if "Unknown" not in recognized_names:
                        print(f"PERSON(S) DETECTED AND RECOGNIZED: {', '.join(recognized_names)}")
                    else:
                        print(f"PERSON(S) DETECTED (including Unknown): {', '.join(recognized_names)}")

                    # Person detected, stop and capture a confirmation image/video
                    print("Person detected. Stopping and capturing confirmation image...")
                    self.scout_bot.stop() # Ensure robot is fully stopped
                    confirmation_image_path = self.scout_camera.capture_image(filename_prefix="person_detected_")
                    print(f"Confirmation image captured: {confirmation_image_path}")

                else:
                    print("No persons detected. Continuing search.")

            except subprocess.CalledProcessError as e:
                print(f"ERROR: Recognition script failed with exit code {e.returncode}. Output: {e.stdout}. Error: {e.stderr}", file=sys.stderr)
            except subprocess.TimeoutExpired:
                print("ERROR: Recognition script timed out after 60 seconds.", file=sys.stderr)
            except FileNotFoundError:
                print(f"ERROR: Python interpreter or recognition script not found. Check paths: {RECOGNIZER_VENV_PYTHON}, {RECOGNIZER_SCRIPT_PATH}", file=sys.stderr)
            except Exception as e:
                print(f"ERROR: An unexpected error occurred during recognition: {e}", file=sys.stderr)

            if person_found:
                break # Exit search loop if person detected

            # 4. Turn (if no person found)
            print("Turning randomly...")
            self.scout_bot.stop() # Ensure robot is stopped before turning
            random_turn_duration = random.uniform(0.3, TURN_DURATION) # Randomize turn duration
            
            if random.random() < 0.5: # 50% chance to turn left, 50% to turn right
                self.scout_bot.left(duration=random_turn_duration)
                print(f"Turned left for {random_turn_duration:.2f} seconds.")
            else:
                self.scout_bot.right(duration=random_turn_duration)
                print(f"Turned right for {random_turn_duration:.2f} seconds.")
            self.scout_bot.stop() # Ensure stop after turn
            
            # Small delay before next iteration to allow robot to stabilize
            time.sleep(1)

        if person_found:
            print("\n--- Person Detected. Search Complete. ---")
        else:
            print("\n--- Max iterations reached. No person found. Search Complete. ---")

    def cleanup(self):
        """Cleans up robot and camera resources."""
        self.scout_bot.cleanup()
        self.scout_camera.cleanup()
        print("SearchBot resources cleaned up.")

# --- Main Execution Block ---
if __name__ == '__main__':
    search_bot = SearchBot()
    try:
        search_bot.search_for_person()
    except KeyboardInterrupt:
        print("\nSearch interrupted by user.")
    finally:
        search_bot.cleanup()
