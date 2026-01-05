from picamera2 import Picamera2
from time import sleep

print("Attempting to initialize the camera...")

try:
    # Create an instance of the camera
    picam2 = Picamera2()
    
    # Configure it for a simple preview
    picam2.configure(picam2.create_preview_configuration())
    
    # Start the camera
    picam2.start()
    
    print("Camera initialized successfully!")
    print("Running for 2 seconds...")
    
    # Keep the camera running for 2 seconds
    sleep(2)
    
    # Stop the camera
    picam2.stop()
    print("Camera stopped.")

except Exception as e:
    print(f"An error occurred: {e}")
    print("\nTroubleshooting:")
    print("1. Ensure the camera is enabled in 'sudo raspi-config' -> Interface Options.")
    print("2. Check the physical ribbon cable connection at both ends (Pi and camera).")
    print("3. Make sure the blue tab on the ribbon cable is facing the USB/Ethernet ports.")
    
finally:
    # Ensure the camera object is closed if it was created
    if 'picam2' in locals() and picam2.is_open:
        picam2.close()
        
    print("\nTest complete.")

