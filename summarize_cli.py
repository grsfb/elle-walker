import google.generativeai as genai
from dotenv import load_dotenv
from PIL import Image
import os
import sys
import time
from google.api_core.exceptions import ResourceExhausted

def _initialize_gemini():
    """Handles the initialization and configuration of the Gemini model."""
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("ERROR: GEMINI_API_KEY not found in .env file.")
    
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-flash-latest')
    return model

def ask_gemini_text(prompt):
    """
    Sends a text-only prompt to the Gemini model and returns the text response.
    """
    try:
        model = _initialize_gemini()
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        error_msg = f"ERROR: An unexpected error occurred during text generation: {e}"
        print(error_msg, file=sys.stderr)
        return error_msg

def summarize_image(image_path, prompt):
    """
    Sends an image and a text prompt to the Gemini model and returns the response.
    """
    try:
        model = _initialize_gemini()
    except Exception as e:
        return str(e)

    if not os.path.exists(image_path):
        return f"Error: Image file not found at {image_path}"

    try:
        img = Image.open(image_path)
    except Exception as e:
        return f"Error: Could not open image file. Details: {e}"

    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = model.generate_content([prompt, img])
            return response.text
        except ResourceExhausted as e:
            if attempt < max_retries - 1:
                print(f"Quota exceeded. Retrying in 60 seconds... (Attempt {attempt + 1}/{max_retries})", file=sys.stderr)
                time.sleep(60)
            else:
                print("Quota exceeded. All retries failed.", file=sys.stderr)
                return f"Error during AI summarization: {e}"
        except Exception as e:
            return f"An unexpected error occurred during summarization: {e}"

# --- Main Execution Block for Standalone Testing ---
if __name__ == '__main__':
    # This block is now only for direct command-line testing of summarize_image
    if len(sys.argv) != 2:
        print("Usage: python summarize_cli.py <image_path>", file=sys.stderr)
        sys.exit(1)
        
    image_path_arg = sys.argv[1]
    custom_prompt = "Describe what is happening in this picture in one, simple sentence."
    
    summary = summarize_image(image_path_arg, custom_prompt)
    
    print(summary)
