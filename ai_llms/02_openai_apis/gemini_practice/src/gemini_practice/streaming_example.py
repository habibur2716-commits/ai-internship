import os
from dotenv import load_dotenv
from google import genai

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

# Streaming wala function - generate_content_stream
response = client.models.generate_content_stream(
    model="gemini-flash-latest",
    contents="gym krna ka faida bato, 100 words mein"
)

for chunk in response:
    print(chunk.text, end="")