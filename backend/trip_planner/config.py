import os
from dotenv import load_dotenv

load_dotenv()

WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
MODEL_NAME = os.getenv("MODEL_NAME", "llama3-8b-8192")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
ORS_API_KEY = os.getenv("ORS_API_KEY")
SERPAPI_KEY = os.getenv("SERPAPI_KEY")
TRAVELPAYOUTS_TOKEN = os.getenv("TRAVELPAYOUTS_TOKEN")
