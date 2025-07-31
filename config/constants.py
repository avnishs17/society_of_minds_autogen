import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Model Name
MODEL_NAME = 'gemini-2.5-flash'
# Get the API key from environment variables
API_KEY = os.getenv('GOOGLE_API_KEY')

if not API_KEY:
    raise ValueError("GOOGLE_API_KEY not found in environment variables. Please set it in your .env file.")
