"""
Script to list available Gemini models.
"""
import google.generativeai as genai
from config import config

# Configure API
genai.configure(api_key=config.GEMINI_API_KEY)

# List models
print("Available Gemini models:")
print("=" * 60)
for model in genai.list_models():
    if 'generateContent' in model.supported_generation_methods:
        print(f"Model: {model.name}")
        print(f"  Display Name: {model.display_name}")
        print(f"  Supported methods: {model.supported_generation_methods}")
        print()
