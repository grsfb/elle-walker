# Work Log for Elle Walker Project

This document chronicles the development process, decisions made, features implemented, and blockers encountered during the creation and enhancement of the "Scout" robot software.

---

## 1. Project Overview (Initial State)

The project aims to build a Raspberry Pi-based autonomous robot ("Scout") capable of:
- Autonomous movement.
- Capturing images/video.
- Detecting and identifying people.
- Using an LLM to summarize visual data.
- Reporting via web interface.

(Based on `PROJECT_PLAN.md`)

---

## 2. Initial Setup & Debugging - Web Control & Summarizer

### Problem 1.1: Web Server Not Working (Flask `ModuleNotFoundError`)
- **User Reported:** "its not working", "connecting ip address not working from mac".
- **Diagnosis:** `web_control.py` failed with `ModuleNotFoundError: No module named 'flask'`. `Flask` was not installed in the Python environment.
- **Solution:** Instructed user to create a virtual environment (`.web_venv`) and `pip install flask`.
- **Outcome:** `web_control.py` successfully started the Flask server.

### Problem 1.2: Mac Cannot Reach Pi Web Server
- **User Reported:** `http://192.168.1.202:5000` not reachable from Mac.
- **Diagnosis:** Server logs showed it was running on `0.0.0.0:5000`. User confirmed `curl http://192.168.1.202:5000` worked on Mac, indicating network connectivity was fine, but a specific browser was failing.
- **Solution:** Advised user to try a different browser.
- **Outcome:** Web server successfully accessible from Mac.

### Problem 1.3: Summarizer Script Failure (`summarize_cli.py`)
- **User Reported:** `subprocess failed` during `/find_person` call, with `recognize_cli.py` working but summarizer failing.
- **Diagnosis (Initial):s` when running `search_cli.py` in `.facerec_venv`.
- **Diagnosis:** `motor_control.py` (imported by `search_cli.py`) requires `gpiozero`, which was missing from the `.facerec_venv`. `picamera2` was also missing.
- **Solution:** Creating a new `.search_venv` for `search_cli.py` to isolate its dependencies. This is a better practice.
- **Outcome:** `search_cli.py` will run in its own virtual environment (`.search_venv`) which contains `gpiozero` and `picamera2`. It will still call `recognize_cli.py` explicitly using the Python from `.facerec_venv`.

---
**Next Steps (as per PROJECT_PLAN.md):**

The next step is to **"Write a 'search' script where the robot roams from room to room until it detects a person."** (from Phase 4). This involves integrating motor control with the current vision system.