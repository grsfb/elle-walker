# This script is designed to demonstrate the numpy version conflict on Bookworm.

print("--- NumPy Conflict Test ---")

# First, let's import a library that uses the NEW numpy we just installed with pip.
# This will load the new numpy (e.g., v2.x) into memory.
print("Importing 'cv2' (opencv), which brings in the NEW numpy from our venv...")
try:
    import cv2
    import numpy as np
    print(f"Success. The active numpy version is now: {np.__version__}")
except Exception as e:
    print(f"Failed to import cv2: {e}")
    # If this fails, we can't even start the test.
    exit()

print("\nNow, let's try to import 'picamera2', which was built by the OS")
print("and expects the OLD system numpy (e.g., v1.24.2)...")

try:
    # This import will trigger the conflict.
    # picamera2's dependency (simplejpeg) will see the new numpy we already loaded
    # and fail because its internal C code was compiled against the old numpy.
    from picamera2 import Picamera2
    print("\nThis message should not appear if the conflict exists.")

except ValueError as e:
    print("\nSUCCESSFULLY CAUGHT THE EXPECTED ERROR:")
    print("-----------------------------------------")
    print(f"ERROR: {e}")
    print("-----------------------------------------")
    print("\nThis proves that a library expecting the new numpy (cv2) cannot coexist")
    print("in the same script with a library expecting the old numpy (picamera2).")

except Exception as e:
    print(f"An unexpected error occurred: {e}")
