# config.py
from dotenv import load_dotenv
import os

# Load environment variables from .env
load_dotenv()

# Get API key
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Check if key loaded correctly
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found. Check your .env file!")
