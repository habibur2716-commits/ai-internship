import os
from dotenv import load_dotenv
from google import genai

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

def get_weather(city: str) -> str:
    """Kisi bhi city ka current mausam batata hai"""
    fake_weather_data = {
        "Lahore": "35°C, Sunny",
        "Karachi": "32°C, Humid",
        "Islamabad": "28°C, Cloudy"
    }
    return fake_weather_data.get(city, "Data not available")

# AI ko function ke baare mein batana
response = client.models.generate_content(
    model="gemini-flash-latest",
    contents="Islamabad aur Lahore aur Karachi ka mausam kaisa hai?",
    config={
        "tools": [get_weather]
    }
)

print(response.text)