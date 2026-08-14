import os
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

# Image file ko padhna
with open("test_image.png", "rb") as f:
    image_bytes = f.read()

response = client.models.generate_content(
    model="gemini-flash-latest",
    contents=[
        types.Part.from_bytes(data=image_bytes, mime_type="image/png"),
        "Is image mein kya hai? Detail mein batao english ma."
    ]
)

print(response.text)