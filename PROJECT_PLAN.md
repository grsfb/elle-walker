# Project Plan: Autonomous "Scout" Robot

This document outlines the development phases for building an autonomous robot capable of navigation and person recognition.

---

### Phase 1: Basic Setup & Motor Control
- **[DONE]** Initial project setup and dependency management.
- **[DONE]** Implement `motor_control.py` to provide a clear class for controlling robot movement (forward, backward, left, right, stop).
- **[DONE]** Test basic motor functions.

---

### Phase 2: Vision System
- **[DONE]** Implement `camera_module.py` using `picamera2` for reliable image and video capture.
- **[DONE]** Create `encode_faces.py` to build a database of known face encodings.
- **[DONE]** Implement `recognize_cli.py` to perform person detection (YOLO), face recognition, and appearance-based Re-ID on a given image.

---

### Phase 3: Sensory Input
- **[DONE]** Implement and test ultrasonic sensor for distance measurement.
- **[DONE]** Resolve low-level hardware conflicts between sensor and motor libraries.

---

### Phase 4: Autonomous Behavior
- **[DONE]** Implement `autonomous_travel.py` for basic obstacle avoidance using the ultrasonic sensor.
- **[DONE]** Implement `search_cli.py` to perform a targeted search mission. This script integrates:
    - Autonomous roaming and obstacle avoidance.
    - Image capture via `ScoutCamera`.
    - Calling the recognition script to find a specific person by name.

---

### Phase 5: User Interface & Interaction (In Progress / Next Steps)
- **[IN PROGRESS]** `web_control.py`: A web interface for manual control and viewing status.
- **[TODO]** `wake_word_listener.py` and `speech_to_text.py`: For voice command capabilities.
- **[TODO]** Integrate UI (web or voice) to trigger the "find person" mission.

---

## 6. Future Enhancements
- **[TODO]** Upgrade to a 3-sensor (left, center, right) ultrasonic array for improved navigation.
- **[TODO]** Add a rear-facing sensor to prevent collisions when backing up.
- **[TODO]** Integrate downward-facing IR sensors to detect drop-offs (e.g., stairs).
