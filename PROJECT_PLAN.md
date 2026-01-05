# Project: "Scout" - The Home Explorer Robot

This document outlines the project plan for building a Raspberry Pi-based home robot that can navigate, observe, and report on activities within the home.

## 1. Project Overview

The goal is to create an autonomous mobile robot named "Scout". Scout will be able to:
- Move around a home environment on wheels.
- Navigate to specific rooms or search for individuals (e.g., a child).
- Capture images or short video clips of the environment.
- Use a Large Language Model (LLM) to analyze the visual data and generate a text summary of the activity.
- Deliver this summary to the user, either through audio playback or a web interface.

## 2. Phases of Development

### Phase 1: Project Scaffolding & Hardware Selection

**Objective:** Define the project structure, select all necessary components, and set up the basic development environment.

**Tasks:**
- **Hardware Bill of Materials (BOM):**
    - **Compute:** Raspberry Pi 5
    - **Power:** USB-C Power Adapter for Pi, Portable Power Bank (for untethered operation), Battery holders.
    - **Chassis:** A 2-wheel or 4-wheel drive robot chassis kit.
    - **Motors & Wheels:** DC motors and wheels (usually part of the chassis kit).
    - **Motor Controller:** An H-Bridge motor driver (like the L298N) to interface between the Pi and the motors.
    - **Camera:** Raspberry Pi Camera Module.
    - **Sensors (for later phases):**
        - Ultrasonic Sensors (for obstacle avoidance).
        - (Optional) LiDAR for mapping (more advanced).
    - **Audio (for later phases):**
        - USB Microphone (for "wake-up word" and voice commands).
        - Small speaker.
    - **Display (for later phases):**
        - Small LCD/OLED Screen (e.g., via SPI/I2C).
- **Software & Technology Stack:**
    - **Operating System:** Raspberry Pi OS (64-bit).
    - **Programming Language:** Python.
    - **Key Libraries:**
        - `gpiozero` or `RPi.GPIO` for motor control.
        - `picamera2` for camera interaction.
        - `OpenCV` for basic image processing and person detection.
        - `Flask` or `FastAPI` for creating a web-based control interface.
        - `requests` for making API calls to an LLM.
        - `Slam-toolbox` or similar for SLAM (advanced).

### Phase 2: Basic Mobility & Remote Control (MVP)

**Objective:** Assemble the robot and control its movements remotely.

**Tasks:**
1.  Assemble the robot chassis, attaching motors, wheels, and mounting the Raspberry Pi and motor driver.
2.  Wire the motor driver to the Raspberry Pi's GPIO pins and to the motors.
3.  Write a Python script to control the motors (forward, backward, left, right).
4.  Set up the camera and write a script to capture and save an image.
5.  Create a simple web application (using Flask) that provides buttons to control the robot's movement and trigger image capture.

### Phase 3: Autonomous Navigation & Mapping

**Objective:** Enable the robot to move around on its own without bumping into things.

**Tasks:**
1.  Integrate ultrasonic sensors to detect obstacles.
2.  Implement a basic obstacle avoidance algorithm (e.g., "if obstacle ahead, stop, turn right, and continue").
3.  **(Advanced) Implement SLAM (Simultaneous Localization and Mapping):** Create a 2D map of your home to enable intelligent path planning and "Travel Mode".
    - *Note: The plan is to use LiDAR-based SLAM, as it is more reliable and less computationally expensive for the Raspberry Pi than camera-based vSLAM.*
4.  **(Advanced) Implement Camera Tilt Mechanism:** Integrate a servo motor and pan-tilt bracket to allow the camera to scan vertically, making person detection more robust.

### Phase 4: Person Detection & Data Capture

**Objective:** Give Scout the ability to find and "see" a person.

**Tasks:**
1.  Use a pre-trained computer vision model (e.g., YOLOv8, or Haar Cascades from OpenCV) to detect people in the camera feed.
2.  **Develop Search Strategy Logic:**
    - **"Travel Mode":** Write logic for navigating between pre-defined waypoints on the map. During travel, a low-frequency "Passive Scan" will run (e.g., checking one frame every 2 seconds) to opportunistically detect the target person without slowing down movement.
    - **"Search Mode":** Write the script for the "Pan-and-Scan" routine. This is a thorough, stationary search where the robot stops at a waypoint and actively pans left and right (and later, tilts up and down) to find the target.
3.  Once a person is detected, the robot will stop and capture a clear image or a short 5-second video clip.

### Phase 5: AI Integration for Summarization

**Objective:** Use an AI model to understand the captured image/video.

**Tasks:**
1.  Choose a multimodal LLM API (e.g., Gemini API).
2.  Write a Python function that sends the captured image/video and a prompt (e.g., "Describe what this person is doing in a short sentence.") to the LLM API.
3.  Process the API response to extract the text summary.

### Phase 6: User Interface & Reporting

**Objective:** Deliver the final summary to the user and complete the mission loop.

**Tasks:**
1.  **Web Interface:** Create a page in the web app where the latest summary and the corresponding image/video can be viewed.
2.  **Audio Output:**
    - Connect a speaker to the Raspberry Pi.
    - Use a Text-to-Speech (TTS) library (like `gTTS`) to convert the summary text into an audio file.
    - Write a script to play the audio file on the robot.
3.  **Wake-up Word Activation:**
    - Use the microphone and a lightweight speech recognition library (e.g., `Porcupine`, `vosk`) to enable hands-free activation of the robot's search mission.
4.  **On-board Display Screen:**
    - Integrate a small LCD or OLED screen to show the robot's current status, IP address, or simple results.
5.  **Bringing it all together:** Create the main application loop:
    - Listen for a command (e.g., a button press in the web app or a spoken wake-up word).
    - **Save current location as "Home".**
    - Start the "search" routine (traveling between waypoints).
    - Once the person is found and data is captured, call the LLM for a summary.
    - **Navigate back to the "Home" location.**
    - Report the summary (either via web, display, or audio).

## 3. Task Hierarchy & Estimates

This provides a rough estimate. "Effort" is a relative measure, not necessarily hours.

| Phase | Task                               | Effort (1-5) |
|-------|------------------------------------|--------------|
| 1     | Hardware Research & Purchase       | 2            |
| 1     | RPi Setup & OS Install             | 1            |
| 2     | Chassis Assembly & Wiring          | 3            |
| 2     | Basic Motor Control Script         | 2            |
| 2     | Remote Control Web App             | 4            |
| 3     | Obstacle Avoidance w/ Sensors      | 4            |
| 3     | SLAM Implementation (Advanced)     | 5+           |
| 4     | Person Detection with OpenCV       | 4            |
| 4     | "Search" Routine Logic           | 3            |
| 5     | LLM API Integration                | 2            |
| 6     | Update Web UI with Summary         | 3            |
| 6     | Text-to-Speech Implementation      | 2            |

---
