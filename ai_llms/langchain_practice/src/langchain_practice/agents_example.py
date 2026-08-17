import os
from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

llm = ChatGoogleGenerativeAI(model="gemini-flash-latest", google_api_key=api_key)

def get_weather(city: str) -> str:
    """Kisi city ka mausam batata hai"""
    weather_data = {"Lahore": "35°C, Sunny", "Karachi": "32°C, Humid"}
    return weather_data.get(city, "Data not available")

def convert_celsius_to_fahrenheit(celsius: float) -> str:
    """Celsius ko Fahrenheit mein convert karta hai"""
    fahrenheit = (celsius * 9/5) + 32
    return f"{fahrenheit}°F"

agent = create_agent(model=llm, tools=[get_weather, convert_celsius_to_fahrenheit])

result = agent.invoke({"messages": [{"role": "user", "content": "Lahore ka mausam kitna hai, Fahrenheit mein bhi batao"}]})
print(result["messages"][-1].content)