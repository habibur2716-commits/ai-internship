import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, AIMessage

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

llm = ChatGoogleGenerativeAI(model="gemini-flash-latest", google_api_key=api_key)

# History khud maintain karte hain (simple tareeqa)
history = []

# Pehla message
history.append(HumanMessage(content="Mera naam Habib hai"))
response1 = llm.invoke(history)
print("AI:", response1.content)
history.append(AIMessage(content=response1.content))

# Doosra message - purani history ke sath
history.append(HumanMessage(content="Mera naam kya hai?"))
response2 = llm.invoke(history)
print("AI:", response2.content)