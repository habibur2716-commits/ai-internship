import os
from dotenv import load_dotenv
from google import genai

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

chat = client.chats.create(model="gemini-flash-latest")

response1 = chat.send_message("Mera naam Habib hai aur main Lahore mein rehta hoon")
print("AI:", response1.text)

response2 = chat.send_message("Mera naam kya hai?")
print("AI:", response2.text)

response3 = chat.send_message("Main kis city mein rehta hoon?")
print("AI:", response3.text)