import vosk
import sounddevice as sd
import json
import time
import sys
import os
import queue
import numpy as np # Still needed for raw data processing from sounddevice
from pydub import AudioSegment

# --- Configuration ---
# Path to the Vosk model directory (relative to script location)
MODEL_PATH = "models/vosk-model-small-en-us-0.15" 

# Audio stream configuration
MICROPHONE_NATIVE_RATE = 16000 # Microphone's native sample rate
VOSK_MODEL_SAMPLE_RATE = 16000 # Vosk model's required sample rate
DEVICE_ID = 1 # Your microphone's sounddevice index

# Queue for audio data from the callback
q = queue.Queue()

# --- Callback function for sounddevice stream ---
def callback(indata, frames, time_info, status):
    """This is called (in a separate thread) for each audio block."""
    if status:
        print(status, file=sys.stderr)
    # Convert indata buffer to a NumPy array before putting into queue
    # Ensure dtype matches what RawInputStream is configured for (int16)
    q.put(np.frombuffer(indata, dtype='int16').copy())

# --- Vosk Model Initialization ---
if not os.path.exists(MODEL_PATH):
    print(f"ERROR: Vosk model not found at '{MODEL_PATH}'")
    print("Please ensure the model is downloaded, extracted, and placed in the 'models' directory.")
    print("Example: models/vosk-model-small-en-us-0.15/")
    sys.exit(1)

model = vosk.Model(MODEL_PATH)
rec = vosk.KaldiRecognizer(model, VOSK_MODEL_SAMPLE_RATE) 

# --- Main Listener Loop ---
print("\nListening for speech... (Say 'quit' to exit)")
print("Silence will be processed, but only full words/phrases will be printed.")
print(f"Using input device ID: {DEVICE_ID} at {MICROPHONE_NATIVE_RATE} Hz (microphone's native rate).")
print(f"Vosk will receive audio at {VOSK_MODEL_SAMPLE_RATE} Hz (after resampling by pydub).")

try:
    with sd.RawInputStream(samplerate=MICROPHONE_NATIVE_RATE, blocksize=8192, device=DEVICE_ID,
                           dtype='int16', channels=1, callback=callback): 
        
        print("Audio stream opened. Speak now.")
        while True:
            # Get audio data from the queue
            if not q.empty():
                data = q.get() # data is a numpy array (int16) at MICROPHONE_NATIVE_RATE

                # Data is already at VOSK_MODEL_SAMPLE_RATE and correct format
                audio_data_for_vosk = data.tobytes()

                if rec.AcceptWaveform(audio_data_for_vosk):
                    result = json.loads(rec.Result())
                    text = result.get('text', '')
                    if text and text != 'quit':
                        print(f"You said: {text}")
                    elif text == 'quit':
                        print("Exiting speech listener.")
                        break
                else:
                    partial_result = json.loads(rec.PartialResult())
                    if partial_result.get('partial', ''):
                        # print(f"Partial: {partial_result['partial']}") # Uncomment for real-time partial feedback
                        pass

except KeyboardInterrupt:
    print("\nSpeech listener stopped by user.")
except Exception as e:
    print(f"An error occurred: {e}", file=sys.stderr)
finally:
    print("Speech listener cleanup complete.")
