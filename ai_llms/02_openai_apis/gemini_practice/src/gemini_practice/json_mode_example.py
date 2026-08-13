import os
import json
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

response = client.models.generate_content(
    model="gemini-flash-latest",
    contents="3 fictional muslim students ki list do JSON format mein, har ek ka name, age, aur favorite subject",
    config=types.GenerateContentConfig(
        response_mime_type="application/json"
    )
)

print(response.text)

# Ab ise Python dictionary mein convert karte hain
data = json.loads(response.text)

# Pehla student (index 0)
print(data[0]["name"])
print(data[0]["age"])

# Ya sab students ko loop se dekho
for student in data:
    print(f"Naam: {student['name']}, Age: {student['age']}, Subject: {student['favorite_subject']}")