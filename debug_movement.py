# debug_movement.py
# A minimal script to test motor movement with the distance sensor initialized.

from motor_control import ScoutBot
from gpiozero import DistanceSensor
from gpiozero.pins.rpigpio import RPiGPIOFactory # Use RPi.GPIO pin factory
from time import sleep

print("--- Starting Minimal Movement Debug Test ---")

try:
    # 1. Create a single, shared pin factory
    print("Step 1: Creating shared RPiGPIOFactory...")
    factory = RPiGPIOFactory()

    # 2. Initialize the Distance Sensor
    print("Step 2: Initializing DistanceSensor...")
    sensor = DistanceSensor(
        echo=24,
        trigger=23,
        pin_factory=factory
    )
    print(f"  -> Sensor initialized. Current distance: {sensor.distance * 100:.2f} cm")

    # 3. Initialize the ScoutBot (motors)
    print("Step 3: Initializing ScoutBot...")
    scout = ScoutBot(pin_factory=factory)
    print("  -> ScoutBot initialized.")

    # 4. Attempt to move forward
    print("\nStep 4: Attempting to move forward at full speed for 3 seconds...")
    scout.forward(speed=1.0)
    sleep(3)
    
    # 5. Stop the robot
    print("Step 5: Stopping motors.")
    scout.stop()

    print("\n--- Test Complete ---")

finally:
    print("Cleaning up GPIO resources...")
    # The cleanup is handled by ScoutBot's cleanup method, which is
    # part of the larger script. Here we can just close the robot.
    if 'scout' in locals():
        scout.cleanup()
    if 'sensor' in locals():
        sensor.close()
    print("Cleanup finished.")
