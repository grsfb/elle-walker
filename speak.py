import pyttsx3
import sys

# Initialize the TTS engine
engine = None
try:
    # We explicitly initialize with the espeak driver
    engine = pyttsx3.init(driverName='espeak')
    print("--- TTS Engine Initialized Successfully ---")
    
except Exception as e:
    print(f"ERROR: Failed to initialize TTS engine: {e}", file=sys.stderr)
    sys.exit(1) # Exit if the engine fails to start

def say(text):
    """
    Uses the TTS engine to speak the given text aloud.
    """
    if not engine:
        print("ERROR: TTS engine not available.", file=sys.stderr)
        return
        
    print(f"Saying: '{text}'")
    try:
        engine.say(text)
        engine.runAndWait()
    except Exception as e:
        print(f"ERROR: Failed to speak text: {e}", file=sys.stderr)

# --- Main Execution Block for Testing ---
if __name__ == '__main__':
    if engine:
        # Test with a default phrase
        print("Testing speaker with a default phrase.")
        say("Hello, my name is lulu. My text to speech engine is working correctly.")
