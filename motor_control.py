from gpiozero import Robot, Motor
from gpiozero.pins.rpigpio import RPiGPIOFactory # Use RPi.GPIO pin factory
from time import sleep

# ===========================================================================
# MOTOR DRIVER WIRING (Assumes L298N-style driver)
# ===========================================================================
# This is a placeholder for when you get your chassis and motor driver.
# You will connect the GPIO pins on your Raspberry Pi to the corresponding
# input pins on the motor driver.

# Left Motor Pins (Swapped to correct rotation)
LEFT_MOTOR_FORWARD_PIN = 21   # Was 20
LEFT_MOTOR_BACKWARD_PIN = 20  # Was 21
LEFT_MOTOR_ENABLE_PIN = 16    # Connected to ENA on the motor driver

# Right Motor Pins
RIGHT_MOTOR_FORWARD_PIN = 19  # Connected to IN3 on the motor driver
RIGHT_MOTOR_BACKWARD_PIN = 26 # Connected to IN4 on the motor driver
RIGHT_MOTOR_ENABLE_PIN = 13   # Connected to ENB on the motor driver
# ===========================================================================

class ScoutBot:
    """
    A class to control the robot's movement, simplified to use gpiozero's
    built-in PWM handling for the Robot class.
    """
    def __init__(self, pin_factory=None):
        # Use a provided pin_factory or create a new one. This allows sharing
        # the factory between multiple devices.
        if pin_factory is None:
            pin_factory = RPiGPIOFactory()
        
        # Create individual Motor objects for left and right,
        # passing the enable pin for PWM control.
        left_motor = Motor(
            forward=LEFT_MOTOR_FORWARD_PIN,
            backward=LEFT_MOTOR_BACKWARD_PIN,
            enable=LEFT_MOTOR_ENABLE_PIN,
            pin_factory=pin_factory
        )
        right_motor = Motor(
            forward=RIGHT_MOTOR_FORWARD_PIN,
            backward=RIGHT_MOTOR_BACKWARD_PIN,
            enable=RIGHT_MOTOR_ENABLE_PIN,
            pin_factory=pin_factory
        )
        
        # Pass the Motor objects to the Robot constructor.
        self.robot = Robot(left=left_motor, right=right_motor)
        print("Robot initialized.")

    def forward(self, speed=1, duration=None):
        """Makes the robot move forward."""
        print(f"Moving forward at speed {speed}...")
        self.robot.forward(speed=speed)
        if duration:
            sleep(duration)
            self.stop()

    def backward(self, speed=1, duration=None):
        """Makes the robot move backward."""
        print(f"Moving backward at speed {speed}...")
        self.robot.backward(speed=speed)
        if duration:
            sleep(duration)
            self.stop()

    def left(self, speed=1, duration=None):
        """Makes the robot turn left."""
        print(f"Turning left at speed {speed}...")
        self.robot.left(speed=speed)
        if duration:
            sleep(duration)
            self.stop()

    def right(self, speed=1, duration=None):
        """Makes the robot turn right."""
        print(f"Turning right at speed {speed}...")
        self.robot.right(speed=speed)
        if duration:
            sleep(duration)
            self.stop()

    def stop(self):
        """Stops the robot."""
        print("Stopping.")
        self.robot.stop()

    def cleanup(self):
        """Cleans up the GPIO resources."""
        print("Disabling motors and cleaning up GPIO...")
        self.robot.close() # This handles stopping and cleaning up all pins.
        print("GPIO resources cleaned up.")


# ===========================================================================
# EXAMPLE USAGE
# ===========================================================================
# This block will only run when you execute the script directly,
# e.g., by running `python motor_control.py` in your terminal.
if __name__ == '__main__':
    # Create an instance of our robot
    scout = ScoutBot()
    
    try:
        # --- Test Sequence ---
        # Since you don't have the hardware yet, this will just print messages.
        # Once your robot is wired, you would see it move.
        
        print("\n--- Starting Robot Test Sequence ---")
        
        # Move forward for 2 seconds
        scout.forward(duration=2)
        
        # Move backward for 2 seconds
        scout.backward(duration=2)
        
        # Turn left for 1 second
        scout.left(duration=1)
        
        # Turn right for 1 second
        scout.right(duration=1)
        
        print("\n--- Test Sequence Complete ---")

    except KeyboardInterrupt:
        # This allows you to stop the script with Ctrl+C
        print("\nProgram stopped by user.")
    
    finally:
        # This will always run, ensuring the GPIO pins are released.
        scout.cleanup()
