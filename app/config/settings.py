import os
from dotenv import load_dotenv

# Load env file
load_dotenv(dotenv_path=".env")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
CHROMA_DB_PATH = os.getenv("CHROMA_DB_PATH", "chroma_store")
GEMINI_MODEL_NAME = os.getenv("GEMINI_MODEL", "models/gemini-pro")
