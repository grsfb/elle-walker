import vosk
import sounddevice as sd
import json
import queue
import os
import sys
import numpy as np
from pydub import AudioSegment
import subprocess

# Import our custom modules
from camera_module import ScoutCamera
from summarize_cli import summarize_image, ask_gemini_text

# --- Configuration ---
WAKE_WORD = "lulu"
MODEL_PATH = "models/vosk-model-small-en-us-0.15"
MICROPHONE_DEVICE_INDEX = 1
MICROPHONE_NATIVE_RATE = 44100
VOSK_MODEL_SAMPLE_RATE = 16000

# --- Venv Paths ---
FACEREC_VENV_PYTHON = os.path.expanduser("~/.facerec_venv/bin/python")
RECOGNIZE_SCRIPT_PATH = os.path.expanduser("~/elle-walker/recognize_cli.py")

# --- State ---
listening_for_command = False

# --- Setup ---
q = queue.Queue()

def callback(indata, frames, time_info, status):
    if status:
        print(status, file=sys.stderr)
    q.put(indata.copy())

def handle_command(command_text):
    """
    Processes the command by first triaging it, recognizing faces, and then executing.
    """
    print(f"DEBUG: Triaging command: '{command_text}'")
    
    triage_prompt = (
        "You are a helpful robot's brain. Classify the user's question as 'VISUAL' or 'TEXT'.\n"
        "Examples: 'what do you see?' -> VISUAL. 'what is the capital of France?' -> TEXT.\n"
        f"Question: '{command_text}'"
    )
    
    try:
        intent = ask_gemini_text(triage_prompt).strip().upper()
        print(f"DEBUG: AI intent classification: {intent}")
    except Exception as e:
        print(f"ERROR: Could not triage command: {e}", file=sys.stderr)
        return

    if 'VISUAL' in intent:
        print("ACTION: VISUAL question. Engaging camera.")
        
        # Capture image
        try:
            camera = ScoutCamera()
            image_path = camera.capture_image(filename_prefix="vision_")
            camera.cleanup()
            print(f"Image captured: {image_path}")
        except Exception as e:
            print(f"ERROR: Camera problem: {e}", file=sys.stderr)
            return

        # Recognize faces
        print("ACTION: Recognizing faces...")
        try:
            result = subprocess.run(
                [FACEREC_VENV_PYTHON, RECOGNIZE_SCRIPT_PATH, image_path],
                capture_output=True, text=True, check=True, timeout=30
            )
            names = result.stdout.strip()
            print(f"DEBUG: Recognized faces: '{names}'")
        except Exception as e:
            print(f"WARN: Face recognition failed, proceeding without names. Error: {e}", file=sys.stderr)
            names = ""

        # Construct final prompt with or without name
        final_prompt = command_text
        if names and "Unknown" not in names and "No persons detected" not in names:
            # Clean up names if there are multiple
            name_list = ", ".join(set(n.strip() for n in names.split(',')))
            final_prompt = (
                f"You are looking at a scene. The person or people you see are named {name_list}. "
                f"Answer their question, addressing them by name: '{command_text}'"
            )
            print(f"DEBUG: Generated personalized prompt.")

        # Get visual answer
        print("ACTION: Generating visual answer...")
        answer = summarize_image(image_path, final_prompt)
        
    else: # Default to TEXT
        print("ACTION: TEXT question. Answering from general knowledge.")
        answer = ask_gemini_text(command_text)

    # Print the final answer
    print("\n--- AI Answer ---")
    print(answer)
    print("-----------------\n")


def main():
    global listening_for_command
    
    print("\nInitializing Wake Word Listener (Vosk)...")
    
    if not os.path.exists(MODEL_PATH):
        print(f"ERROR: Vosk model not found at '{MODEL_PATH}'")
        sys.exit(1)

    try:
        model = vosk.Model(MODEL_PATH)
        recognizer = vosk.KaldiRecognizer(model, VOSK_MODEL_SAMPLE_RATE)
        recognizer.SetWords(True)

        print(f"Listening for wake word: '{WAKE_WORD}'")
        
        with sd.InputStream(samplerate=MICROPHONE_NATIVE_RATE, device=MICROPHONE_DEVICE_INDEX,
                               dtype='int16', channels=1, callback=callback):

            while True:
                data = q.get()
                audio_segment = AudioSegment(data.tobytes(), frame_rate=MICROPHONE_NATIVE_RATE, sample_width=data.dtype.itemsize, channels=1)
                resampled_audio_segment = audio_segment.set_frame_rate(VOSK_MODEL_SAMPLE_RATE)
                audio_data_for_vosk = resampled_audio_segment.raw_data

                if recognizer.AcceptWaveform(audio_data_for_vosk):
                    result = json.loads(recognizer.Result())
                    text = result.get('text', '')

                    if not listening_for_command and WAKE_WORD in text:
                        print(f"\nWake word '{WAKE_WORD}' detected!")
                        listening_for_command = True
                        print("Now listening for a command...")
                        recognizer.Reset()
                    elif listening_for_command:
                        if text:
                            print(f"\nCommand received: '{text}'")
                            handle_command(text)
                        else:
                            print("\nNo command detected after wake word.")
                        
                        listening_for_command = False
                        print(f"\nWaiting for wake word '{WAKE_WORD}'...")
                else:
                    partial_result = json.loads(recognizer.PartialResult())
                    partial_text = partial_result.get('partial', '')

                    if not listening_for_command and WAKE_WORD in partial_text:
                        print(f"\nWake word '{WAKE_WORD}' detected!")
                        listening_for_command = True
                        print("Now listening for a command...")
                        recognizer.Reset()

    except KeyboardInterrupt:
        print("\nListener stopped by user.")
    except Exception as e:
        print(f"An error occurred: {e}", file=sys.stderr)
    finally:
        print("Cleanup complete.")

if __name__ == '__main__':
    main()
