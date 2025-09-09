import google.generativeai as genai
from app.config.settings import GEMINI_MODEL_NAME

def generate_response(prompt: str, model_name: str = GEMINI_MODEL_NAME) -> str:
    model = genai.GenerativeModel(model_name)
    response = model.generate_content(prompt)
    return response.text


    
