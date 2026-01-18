
## 2026-01-17

- **`lcd_display.py` & `eye_daemon.py`**:
  - Overhauled and repaired face display logic.
  - Restored full face animations (eyebrows, mouth).
  - Disabled conflicting `eye_daemon.py` script to prevent rendering issues.
  - Fixed a bug where long-answer smiley animations would not display due to duplicated and broken function definitions.
  - Re-implemented stateful message handling, allowing short text answers to be displayed correctly on the screen for a set duration.
- **System**:
  - Confirmed `main_controller.py` is run using `speech_venv`.
