import google.generativeai as genai
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get the API key from the environment
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("ERROR: GEMINI_API_KEY not found in .env file.")
    exit()

genai.configure(api_key=api_key)

print("--- Available Models ---")
for m in genai.list_models():
  if 'generateContent' in m.supported_generation_methods:
    print(m.name)
print("------------------------")
