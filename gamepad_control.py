import pygame
import time
from motor_control import ScoutBot
from gpiozero import Robot # For type hinting/clarity, not directly used in the script

# --- Configuration ---
# Adjust these values based on your PS5 controller's axis mapping
# You may need to experiment with `jstest` or `evtest` on Linux to confirm axis IDs
# Typical PS5 DualSense mappings (may vary slightly)
LEFT_STICK_Y_AXIS = 1  # Left stick vertical axis (forward/backward)
RIGHT_STICK_X_AXIS = 2 # Right stick horizontal axis (left/right turn)
DEADZONE = 0.1         # Ignore small stick movements near center (0.0 to 1.0)
SPEED_SCALE = 1.0      # Scale joystick input to robot speed (0.0 to 1.0)

# --- Robot Initialization ---
print("Initializing ScoutBot...")
scout_bot = ScoutBot()
print("ScoutBot initialized.")

# --- Pygame and Joystick Initialization ---
print("Initializing Pygame...")
pygame.init()
pygame.display.init() # Needed for some pygame event handling, even if headless
pygame.joystick.init()

try:
    if pygame.joystick.get_count() == 0:
        print("No joystick found. Make sure your PS5 controller is paired and connected.")
        exit()

    joystick = pygame.joystick.Joystick(0) # Get the first joystick
    joystick.init() # Initialize it
    print(f"Detected Joystick: {joystick.get_name()} (ID: {joystick.get_id()})")

    # --- Main Control Loop ---
    running = True
    print("\nRobot control ready. Use left stick for forward/backward, right stick for turning.")
    print("Press Ctrl+C to exit cleanly.")

    while running:
        # Process Pygame events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.JOYBUTTONDOWN:
                print(f"Button {event.button} pressed")
                # Add button actions here if needed (e.g., capture image, start search)
            elif event.type == pygame.JOYBUTTONUP:
                print(f"Button {event.button} released")
            # JOYAXISMOTION events are continuous; we read axis state directly below

        # Read stick values
        left_y_raw = joystick.get_axis(LEFT_STICK_Y_AXIS)
        right_x_raw = joystick.get_axis(RIGHT_STICK_X_AXIS)
        
        # Apply deadzone
        left_y = 0
        if abs(left_y_raw) >= DEADZONE:
            left_y = left_y_raw

        right_x = 0
        if abs(right_x_raw) >= DEADZONE:
            right_x = right_x_raw

        # Map to robot speed values (-1.0 to 1.0)
        forward_speed = -left_y * SPEED_SCALE # Invert Y-axis for intuitive forward
        turn_speed = right_x * SPEED_SCALE

        # Calculate individual motor speeds (tank drive mixing)
        left_motor_speed = max(-1.0, min(1.0, forward_speed - turn_speed))
        right_motor_speed = max(-1.0, min(1.0, forward_speed + turn_speed))
        
        # DEBUG PRINTS
        print(f"Raw: LY={left_y_raw:.3f}, RX={right_x_raw:.3f} | Processed: Fwd={forward_speed:.3f}, Turn={turn_speed:.3f} | Final Motors: L={left_motor_speed:.3f}, R={right_motor_speed:.3f}")

        # Apply to robot
        if abs(forward_speed) > 0 or abs(turn_speed) > 0: # Check if any movement is requested outside deadzone
            scout_bot.robot.value = (left_motor_speed, right_motor_speed)
        else:
            scout_bot.robot.stop() # Stop motors if sticks are in deadzone

        time.sleep(0.05) # Small delay to prevent busy-looping and reduce CPU usage

except KeyboardInterrupt:
    print("\nExiting control.")
except Exception as e:
    print(f"An error occurred: {e}")
finally:
    if 'scout_bot' in locals() and scout_bot is not None:
        scout_bot.robot.stop() # Ensure robot stops on exit
        scout_bot.cleanup()
    pygame.quit()
    print("Cleanup complete.")
