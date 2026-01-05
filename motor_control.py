from gpiozero import Robot, PWMOutputDevice
from time import sleep

# ===========================================================================
# MOTOR DRIVER WIRING (Assumes L298N-style driver)
# ===========================================================================
# This is a placeholder for when you get your chassis and motor driver.
# You will connect the GPIO pins on your Raspberry Pi to the corresponding
# input pins on the motor driver.

# Left Motor Pins
LEFT_MOTOR_FORWARD_PIN = 20   # Connected to IN1 on the motor driver
LEFT_MOTOR_BACKWARD_PIN = 21  # Connected to IN2 on the motor driver
LEFT_MOTOR_ENABLE_PIN = 16    # Connected to ENA on the motor driver

# Right Motor Pins
RIGHT_MOTOR_FORWARD_PIN = 19  # Connected to IN3 on the motor driver
RIGHT_MOTOR_BACKWARD_PIN = 26 # Connected to IN4 on the motor driver
RIGHT_MOTOR_ENABLE_PIN = 13   # Connected to ENB on the motor driver
# ===========================================================================

class ScoutBot:
    """
    A class to control the robot's movement.
    """
    def __init__(self):
        # The gpiozero Robot class takes the left and right motor pins as arguments.
        # It handles the logic for forward, backward, left, and right movements.
        self.robot = Robot(
            left=(LEFT_MOTOR_FORWARD_PIN, LEFT_MOTOR_BACKWARD_PIN),
            right=(RIGHT_MOTOR_FORWARD_PIN, RIGHT_MOTOR_BACKWARD_PIN)
        )
        
        # We use PWMOutputDevice for the enable pins to control speed.
        # For now, we'll just set it to full speed (value=1).
        self.left_motor_speed = PWMOutputDevice(LEFT_MOTOR_ENABLE_PIN)
        self.right_motor_speed = PWMOutputDevice(RIGHT_MOTOR_ENABLE_PIN)
        
        # Set initial speed to maximum
        self.set_speed(1)
        print("Robot initialized.")

    def set_speed(self, speed):
        """
        Sets the speed of the robot.
        :param speed: A value between 0 (stop) and 1 (full speed).
        """
        if 0 <= speed <= 1:
            self.left_motor_speed.value = speed
            self.right_motor_speed.value = speed
            print(f"Speed set to {speed}")
        else:
            print("Speed must be between 0 and 1.")

    def forward(self, duration=None):
        """Makes the robot move forward."""
        print("Moving forward...")
        self.robot.forward()
        if duration:
            sleep(duration)
            self.stop()

    def backward(self, duration=None):
        """Makes the robot move backward."""
        print("Moving backward...")
        self.robot.backward()
        if duration:
            sleep(duration)
            self.stop()

    def left(self, duration=None):
        """Makes the robot turn left."""
        print("Turning left...")
        self.robot.left()
        if duration:
            sleep(duration)
            self.stop()

    def right(self, duration=None):
        """Makes the robot turn right."""
        print("Turning right...")
        self.robot.right()
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
        self.robot.stop()
        self.set_speed(0)
        self.robot.close()
        self.left_motor_speed.close()
        self.right_motor_speed.close()
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
