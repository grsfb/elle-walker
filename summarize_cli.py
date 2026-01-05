# This script uses a multimodal Gemini model to describe an image.
# It is designed to be called from the command line.

import google.generativeai as genai
from dotenv import load_dotenv
from PIL import Image
import os
import sys
import time
from google.api_core.exceptions import ResourceExhausted

# --- Initialization ---

# Load environment variables from .env file
load_dotenv()

# Get the API key from the environment
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("ERROR: GEMINI_API_KEY not found in .env file.", file=sys.stderr)
    sys.exit(1)

# Configure the generative AI model
try:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-flash-latest')
except Exception as e:
    print(f"ERROR: Could not configure Gemini AI. Check your API key. Details: {e}", file=sys.stderr)
    sys.exit(1)


def summarize_image(image_path, prompt):
    """
    Sends an image and a prompt to the Gemini Pro Vision model and returns the response.
    Retries on quota errors.
    """
    if not os.path.exists(image_path):
        return f"Error: Image file not found at {image_path}"

    img = Image.open(image_path)
    max_retries = 3
    
    for attempt in range(max_retries):
        try:
            # Ask the model to describe the image based on the prompt
            response = model.generate_content([prompt, img])
            # Return the generated text
            return response.text
        except ResourceExhausted as e:
            if attempt < max_retries - 1:
                print(f"Quota exceeded. Retrying in 60 seconds... (Attempt {attempt + 1}/{max_retries})", file=sys.stderr)
                time.sleep(60)
            else:
                print("Quota exceeded. All retries failed.", file=sys.stderr)
                return f"Error during AI summarization: {e}"
        except Exception as e:
            # For any other unexpected error, fail immediately.
            return f"An unexpected error occurred during summarization: {e}"


# --- Main Execution Block ---
if __name__ == '__main__':
    # Check for the correct number of command-line arguments
    if len(sys.argv) != 2:
        print("Usage: python summarize_cli.py <image_path>", file=sys.stderr)
        sys.exit(1)
        
    image_path_arg = sys.argv[1]
    
    # Define the prompt we want to send to the model
    custom_prompt = "Describe what is happening in this picture in one, simple sentence."
    
    # Get the summary from the model
    summary = summarize_image(image_path_arg, custom_prompt)
    
    # Print the summary to stdout, so the calling process can capture it
    print(summary)
