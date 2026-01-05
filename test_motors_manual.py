from gpiozero import OutputDevice
from time import sleep

# Initialize pins as OutputDevices with initial state LOW
left_forward = OutputDevice(20, initial_value=False)
left_backward = OutputDevice(21, initial_value=False)
left_enable = OutputDevice(16, initial_value=True)  # Enable = HIGH

right_forward = OutputDevice(19, initial_value=False)
right_backward = OutputDevice(26, initial_value=False)
right_enable = OutputDevice(13, initial_value=True)  # Enable = HIGH

print("Testing motors with explicit pin control...")

try:
    # Test LEFT motor forward
    print("\n1. LEFT motor FORWARD (3 seconds)")
    left_forward.on()
    left_backward.off()
    sleep(3)
    left_forward.off()
    
    sleep(1)
    
    # Test LEFT motor backward
    print("2. LEFT motor BACKWARD (3 seconds)")
    left_forward.off()
    left_backward.on()
    sleep(3)
    left_backward.off()
    
    sleep(1)
    
    # Test RIGHT motor forward
    print("3. RIGHT motor FORWARD (3 seconds)")
    right_forward.on()
    right_backward.off()
    sleep(3)
    right_forward.off()
    
    sleep(1)
    
    # Test RIGHT motor backward
    print("4. RIGHT motor BACKWARD (3 seconds)")
    right_forward.off()
    right_backward.on()
    sleep(3)
    right_backward.off()
    
    sleep(1)
    
    # Test BOTH motors forward
    print("5. BOTH motors FORWARD (3 seconds)")
    left_forward.on()
    left_backward.off()
    right_forward.on()
    right_backward.off()
    sleep(3)
    left_forward.off()
    right_forward.off()
    
    print("\nTest complete!")

except KeyboardInterrupt:
    print("\nStopped by user")

finally:
    # Clean up - set all to LOW
    left_forward.off()
    left_backward.off()
    right_forward.off()
    right_backward.off()
    left_forward.close()
    left_backward.close()
    left_enable.close()
    right_forward.close()
    right_backward.close()
    right_enable.close()
    print("Cleanup complete")
