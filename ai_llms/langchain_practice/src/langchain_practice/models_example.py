import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

# Model banana
llm = ChatGoogleGenerativeAI(model="gemini-flash-latest", google_api_key=api_key)

# Seedha use karna
response = llm.invoke("Pakistan ka capital kya hai?")
print(response.content)