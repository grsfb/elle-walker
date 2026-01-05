# This script is the main brain of the robot, managing its state and actions.
# It implements a two-mode architecture:
# 1. Navigation Mode: Moves around, detects obstacles and people using fast YOLO.
# 2. Identification Mode: Stops and uses the full recognition pipeline to identify a person.

import time
from motor_control import ScoutBot
from camera_module import ScoutCamera
from recognition_service import RecognitionService
import cv2

class RobotController:
    def __init__(self):
        print("Initializing Robot Controller...")
        self.motor = ScoutBot()
        self.camera = ScoutCamera()
        self.recognition = RecognitionService()
        self.current_mode = "NAVIGATION"  # Start in Navigation mode

    def run(self):
        """The main control loop for the robot."""
        print("Starting main control loop...")
        try:
            while True:
                if self.current_mode == "NAVIGATION":
                    self.run_navigation_mode()
                elif self.current_mode == "IDENTIFICATION":
                    self.run_identification_mode()
                else:
                    print(f"Unknown mode: {self.current_mode}. Shutting down.")
                    break
        except KeyboardInterrupt:
            print("\nShutting down robot controller.")
        finally:
            self.motor.cleanup()
            self.camera.cleanup()

    def run_navigation_mode(self):
        print("--- Mode: NAVIGATION ---")
        # In the next step, we will implement this logic:
        # 1. Move forward slightly.
        # 2. Capture an image.
        # 3. Use YOLO to detect objects.
        # 4. If an obstacle is in the way, turn.
        # 5. If a person is detected, switch to IDENTIFICATION mode.
        print("TODO: Implement navigation logic. For now, just waiting.")
        time.sleep(2)
        # For now, we will manually switch mode to test the structure.
        print("Switching to IDENTIFICATION mode for demonstration.")
        self.current_mode = "IDENTIFICATION"


    def run_identification_mode(self):
        print("--- Mode: IDENTIFICATION ---")
        # In a future step, we will implement this logic:
        # 1. Stop motors.
        # 2. Capture a clear image.
        # 3. Run the full recognition service on the image.
        # 4. Announce the name of the person found.
        # 5. Switch back to NAVIGATION mode.
        print("TODO: Implement identification logic. For now, just waiting.")
        time.sleep(5)
        print("Switching back to NAVIGATION mode.")
        self.current_mode = "NAVIGATION"


if __name__ == '__main__':
    controller = RobotController()
    controller.run()
