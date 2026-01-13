
---

## 3. Autonomous Navigation and Targeted Search Implementation

This phase focused on implementing the "find a specific person" feature, which required a deep dive into hardware integration and debugging.

### Problem 3.1: Initial Movement and Sensor Integration
- **Goal:** Combine motor control with the ultrasonic sensor for basic obstacle avoidance.
- **Initial State:** `autonomous_travel.py` existed but had several issues.
- **Debugging Journey:**
    1.  **`gpiozero` Conflicts:** Discovered a low-level conflict between the `Motor` and `DistanceSensor` components that caused the robot's motors to fail when both were active.
    2.  **Pin Factory Investigation:**
        -   `LGPIOFactory` (default for Pi 5) exhibited the conflict.
        -   `PigpioFactory` was attempted, but the `pigpiod` daemon failed to start on the user's system, reporting it was not a Raspberry Pi.
        -   `RPiGPIOFactory` was chosen as the fallback. This led to a `RuntimeError` ("Cannot determine SOC peripheral base address"), which was resolved by running the scripts with `sudo`.
    3.  **Shared Factory:** Refactored all scripts (`motor_control.py`, `autonomous_travel.py`) to ensure all `gpiozero` components shared a single, explicitly passed pin factory instance. This is a critical best practice but did not solve the root conflict.
    4.  **Final Sensor Solution:** The `gpiozero` conflict was deemed unresolvable. `autonomous_travel.py` was rewritten to bypass `gpiozero` for the sensor, using the `RPi.GPIO` library directly to read sensor values. This finally resolved the hardware conflict.
- **Outcome:** The robot successfully moves forward and performs a backup-and-turn maneuver when it detects an obstacle.

### Problem 3.2: Integrating Face Recognition with Movement
- **Goal:** Modify `search_cli.py` to roam and stop only when a specific person is found.
- **Initial State:** The script was a placeholder, designed to find *any* person.
- **Debugging Journey:**
    1.  **Motor Wiring:** The robot was "rotating in place" instead of moving forward. This was diagnosed as one motor being wired backwards.
        -   **Solution:** Swapped the forward/backward pin numbers for the left motor in `motor_control.py`.
    2.  **Camera Integration:** The script failed with a `No such file or directory: 'raspistill'` error.
        -   **Diagnosis:** The user's Pi uses the modern `libcamera` stack, not the legacy `raspistill`.
        -   **Solution:** Modified `search_cli.py` to import and use the `ScoutCamera` class from `camera_module.py`, which correctly uses the `picamera2` library.
    3.  **`sudo` Path Issues:** When running with `sudo`, the home directory shortcut `~` resolved to `/root`, causing the script to fail to find the `.facerec_venv`.
        -   **Solution:** Changed the path generation logic to be relative to the script's own file location, making it robust to `sudo`.
    4.  **Missing Dependencies:** The `recognize_cli.py` script failed due to missing modules (`cv2`, `ultralytics`).
        -   **Solution:** Instructed the user to install the missing packages into the `.facerec_venv`.
    5.  **Recognition Logic Bug:** The search failed because a one-time model download message polluted the script's output, and the name comparison was case-sensitive.
        -   **Solution:** Made the output parsing more robust by only considering the last line of output. Made the name comparison case-insensitive.
- **Outcome:** The `search_cli.py` script now successfully takes a name as an argument, roams while avoiding obstacles, and stops when it correctly identifies the target person.
